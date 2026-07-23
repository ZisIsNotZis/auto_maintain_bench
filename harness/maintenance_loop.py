from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
from typing import Any, Callable, Protocol
from urllib import error, request

from .telemetry_archive import TelemetryArchive


ESCALATION_LEVELS = {
    "uncertain",
    "unlocated",
    "no_fix",
    "temporary",
    "blocked",
    "failed",
    "rollback_failed",
}


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class BashResult:
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class WakeupResult:
    terminal: str
    message: str
    escalation_level: str | None
    escalation_id: str | None
    messages: tuple[dict[str, Any], ...]
    telemetry_path: Path


class ModelTransport(Protocol):
    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: str,
    ) -> dict[str, Any]: ...


class MaintenanceLoop:
    def __init__(
        self,
        *,
        transport: ModelTransport,
        command_executor: Callable[[str], BashResult],
        system_prompt: str,
        bash_tool: dict[str, Any],
        project_readme_path: Path,
        memory_path: Path,
        telemetry_archive: TelemetryArchive,
        max_steps: int = 64,
        max_context_tokens: int = 12000,
        truncate_fraction: float = 0.5,
        project_readme_display_path: str | None = None,
        memory_display_path: str | None = None,
        telemetry_display_dir: str | None = None,
    ) -> None:
        self.transport = transport
        self.command_executor = command_executor
        self.system_prompt = system_prompt
        self.bash_tool = bash_tool
        self.project_readme_path = project_readme_path
        self.memory_path = memory_path
        self.telemetry_archive = telemetry_archive
        self.max_steps = max_steps
        self.max_context_tokens = max_context_tokens
        self.truncate_fraction = truncate_fraction
        self.project_readme_display_path = project_readme_display_path
        self.memory_display_path = memory_display_path
        self.telemetry_display_dir = telemetry_display_dir

    def run_wakeup(self, telemetry: dict[str, Any]) -> WakeupResult:
        telemetry_path = self.telemetry_archive.store(telemetry)
        telemetry_actionable = _telemetry_has_actionable_signals(telemetry)
        messages = [
            {
                "role": "system",
                "content": self._render_system_prompt(),
            },
            {
                "role": "user",
                "content": self._render_user_message(telemetry),
            },
        ]
        audit_messages = list(messages)
        executed_commands: dict[str, BashResult] = {}
        backed_up_paths: set[str] = set()
        evidence_artifacts_written: set[str] = set()
        state_changes = 0
        last_result: BashResult | None = None
        consecutive_readonly_successes = 0
        require_terminal = False
        duplicate_attempts = 0
        for _ in range(self.max_steps):
            messages = truncate_conversation(
                messages,
                max_context_tokens=self.max_context_tokens,
                target_fraction=self.truncate_fraction,
            )
            response = self.transport.complete(
                messages=messages,
                tools=[self.bash_tool],
                tool_choice="required",
            )
            content = str(response.get("content", "") or "")
            reasoning_content = str(response.get("reasoning_content", "") or "")
            calls = response.get("tool_calls") or []
            if len(calls) != 1 or not isinstance(calls[0], ToolCall) or calls[0].name != "bash":
                additions = [
                    _assistant_text_message(content, reasoning_content),
                    {
                        "role": "user",
                        "content": (
                            "Your previous response did not contain exactly one parsed bash "
                            "tool call. Call bash exactly once now. Use ordinary bash to inspect "
                            "or repair, everything_ok after fresh verification, or escalate when "
                            "safe autonomous handling cannot continue."
                        ),
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            call = calls[0]
            command = call.arguments.get("command")
            if not isinstance(command, str) or not command.strip():
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(2, "", "command must be a non-empty string"),
                    ),
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            command = command.strip()
            terminal = _terminal_command(command)
            if terminal is not None:
                kind, level, message = terminal
                if (
                    kind == "everything_ok"
                    and telemetry_actionable
                    and (
                        not executed_commands
                        or state_changes == 0
                    )
                ):
                    additions = [
                        _assistant_tool_message(call, content, reasoning_content),
                        _tool_message(
                            call.id,
                            BashResult(
                                2,
                                "",
                                "everything_ok rejected because actionable telemetry indicates unresolved issues",
                            ),
                        ),
                        {
                            "role": "user",
                            "content": (
                                "Do not call everything_ok yet. Current telemetry contains actionable "
                                "fault signals. Run and verify at least one real state-changing repair "
                                "before terminal."
                            ),
                        },
                    ]
                    messages.extend(additions)
                    audit_messages.extend(additions)
                    continue
                escalation_id = (
                    _escalation_id(level, message)
                    if kind == "escalate" and level not in {None, "none"}
                    else None
                )
                assistant_message = _assistant_tool_message(
                    call,
                    content,
                    reasoning_content,
                )
                messages.append(assistant_message)
                audit_messages.append(assistant_message)
                return WakeupResult(
                    terminal=kind,
                    message=message,
                    escalation_level=level,
                    escalation_id=escalation_id,
                    messages=tuple(audit_messages),
                    telemetry_path=telemetry_path,
                )
            if require_terminal:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "non-terminal command rejected after repeated successful read-only verification",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": (
                            "Do not run more shell commands. Your next bash call must be exactly "
                            "`everything_ok` if repaired, or exactly "
                            "`escalate uncertain verification is insufficient`."
                        ),
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            wrapped_control = _wrapped_terminal_control(command)
            if wrapped_control is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "wrapped daemon control rejected without execution",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": (
                            "That command was not executed. Do not print or shell-wrap a daemon "
                            f"control. Call the bash tool with the bare control value exactly "
                            f"`{wrapped_control}`."
                        ),
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            reread_warning = self._context_reread_warning(command)
            if reread_warning is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "context document reread rejected without execution",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": reread_warning,
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            if command in executed_commands:
                duplicate_attempts += 1
                previous = executed_commands[command]
                warning = (
                    "Stop. Do not call an ordinary shell command again. Call the bash tool "
                    "with command exactly `everything_ok` if the cached results verify the "
                    "repair. Otherwise call the bash tool with command exactly "
                    "`escalate uncertain verification is insufficient`."
                    if duplicate_attempts >= 3
                    else (
                        "That exact bash command was not executed because it already ran "
                        "during this maintenance cycle. The tool response repeats its cached "
                        "prior result. Do not call it again. If existing evidence verifies "
                        "the repair, finish with everything_ok; otherwise choose a different "
                        "inspection or repair, or escalate."
                    )
                )
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            previous.exit_code,
                            previous.stdout,
                            (
                                f"{previous.stderr}\n"
                                "duplicate command was not re-executed; "
                                "this is the cached prior result"
                            ).lstrip(),
                        ),
                    ),
                    {
                        "role": "user",
                        "content": warning,
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            backup_warning = _missing_backup_warning(command, backed_up_paths)
            if backup_warning is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "persistent file mutation rejected because no maint-backup exists in this cycle",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": backup_warning,
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            host_path_warning = _forbidden_host_path_warning(command)
            if host_path_warning is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "host path access rejected without execution",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": host_path_warning,
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            cd_warning = _forbidden_cd_sandbox_warning(command)
            if cd_warning is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "relative path workflow rejected; use absolute /sandbox paths",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": cd_warning,
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            temp_backup_warning = _temp_cache_backup_warning(command)
            if temp_backup_warning is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "temporary cache backup copy rejected; preserve evidence via listing only",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": temp_backup_warning,
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            restore_warning = _premature_restore_warning(command, last_result)
            if restore_warning is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "backup restore rejected because there is no failed verification to justify rollback",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": restore_warning,
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            evidence_warning = _evidence_overwrite_warning(
                command,
                evidence_artifacts_written,
            )
            if evidence_warning is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            "evidence artifact overwrite rejected without execution",
                        ),
                    ),
                    {
                        "role": "user",
                        "content": evidence_warning,
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            result = self.command_executor(command)
            last_result = result
            executed_commands[command] = result
            backed_up = _backup_source_path(command)
            if backed_up is not None and result.exit_code == 0:
                backed_up_paths.add(backed_up)
            evidence_path = _evidence_artifact_write_path(command)
            if evidence_path is not None and result.exit_code == 0:
                evidence_artifacts_written.add(evidence_path)
            if result.exit_code == 0 and _is_state_changing_command(command):
                state_changes += 1
            if result.exit_code == 0 and not _is_state_changing_command(command):
                consecutive_readonly_successes += 1
            else:
                consecutive_readonly_successes = 0
            additions = [
                _assistant_tool_message(call, content, reasoning_content),
                _tool_message(call.id, result),
            ]
            if consecutive_readonly_successes >= 4:
                require_terminal = True
                additions.append(
                    {
                        "role": "user",
                        "content": (
                            "You now have repeated successful read-only verification evidence. "
                            "Do not run more inspection commands. Your next bash call must be "
                            "exactly `everything_ok` if repaired, or exactly "
                            "`escalate uncertain verification is insufficient` if not."
                        ),
                    }
                )
            messages.extend(additions)
            audit_messages.extend(additions)
        return WakeupResult(
            terminal="escalate",
            message="model_exceeded_max_steps_without_terminal_command",
            escalation_level="failed",
            escalation_id=_escalation_id(
                "failed",
                "model_exceeded_max_steps_without_terminal_command",
            ),
            messages=tuple(audit_messages),
            telemetry_path=telemetry_path,
        )

    def _render_system_prompt(self) -> str:
        return self.system_prompt.replace(
            "{{telemetry_log_dir}}",
            self.telemetry_display_dir
            or str(self.telemetry_archive.root.resolve()),
        )

    def _render_user_message(self, telemetry: dict[str, Any]) -> str:
        readme = _read_required_text(self.project_readme_path, "project README")
        memory = (
            self.memory_path.read_text(encoding="utf-8").strip()
            if self.memory_path.is_file()
            else ""
        )
        if memory.lower() in {"# maintenance memory", "maintenance memory"}:
            memory = ""
        readme_path = (
            self.project_readme_display_path
            or str(self.project_readme_path.resolve())
        )
        memory_path = self.memory_display_path or str(self.memory_path.resolve())
        return (
            f"# Project README\nSource: {readme_path}\n\n{readme}\n\n"
            "# Memory\n"
            f"Source: {memory_path}\n\n{memory or '(empty)'}\n\n"
            "# Current telemetry\n"
            f"{json.dumps(telemetry, ensure_ascii=True, indent=2, sort_keys=True)}"
        )

    def _context_reread_warning(self, command: str) -> str | None:
        paths = {
            str(self.project_readme_path.resolve()),
            str(self.memory_path.resolve()),
        }
        if self.project_readme_display_path:
            paths.add(self.project_readme_display_path)
        if self.memory_display_path:
            paths.add(self.memory_display_path)
        lower_command = command.lower()
        for path in paths:
            lower_path = path.lower()
            if lower_path and lower_path in lower_command:
                if "memory" in lower_path:
                    return (
                        "Do not reread MEMORY.md with bash. Its full content is already in the "
                        "first user message under # Memory. Use a different command that inspects "
                        "live host state or performs a repair."
                    )
                return (
                    "Do not reread README.md with bash. Its full content is already in the first "
                    "user message under # Project README. Use a different command that inspects "
                    "live host state or performs a repair."
                )
        return None


class OpenAIModelTransport:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_s: float = 180.0,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        top_p: float = 0.9,
        top_k: int = 40,
        min_p: float = 0.05,
        presence_penalty: float = 0.05,
        frequency_penalty: float = 0.05,
        seed: int = 42,
        repeat_penalty: float = 1.05,
        repeat_last_n: int = 256,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.min_p = min_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.seed = seed
        self.repeat_penalty = repeat_penalty
        self.repeat_last_n = repeat_last_n

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: str,
    ) -> dict[str, Any]:
        body = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "min_p": self.min_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "seed": self.seed,
            "repeat_penalty": self.repeat_penalty,
            "repeat_last_n": self.repeat_last_n,
            "max_tokens": self.max_tokens,
        }
        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout_s) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code == 500 and "peg-native format" in detail:
                return {
                    "content": "",
                    "reasoning_content": "",
                    "finish_reason": "server_format_error",
                    "tool_calls": [],
                }
            raise RuntimeError(f"model HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"model endpoint unreachable: {exc}") from exc
        choice = (payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        calls: list[ToolCall] = []
        for raw in message.get("tool_calls") or []:
            function = raw.get("function") if isinstance(raw.get("function"), dict) else {}
            arguments = function.get("arguments", "{}")
            try:
                parsed = json.loads(arguments) if isinstance(arguments, str) else arguments
            except json.JSONDecodeError:
                parsed = {}
            calls.append(
                ToolCall(
                    id=str(raw.get("id", "")),
                    name=str(function.get("name", "")),
                    arguments=parsed if isinstance(parsed, dict) else {},
                )
            )
        return {
            "content": str(message.get("content", "") or ""),
            "reasoning_content": str(message.get("reasoning_content", "") or ""),
            "finish_reason": str(choice.get("finish_reason", "") or ""),
            "tool_calls": calls,
        }


def execute_bash(
    command: str,
    *,
    cwd: Path,
    timeout_s: float = 60.0,
    max_output_chars: int = 20000,
) -> BashResult:
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return BashResult(
            exit_code=124,
            stdout=(exc.stdout or "")[-max_output_chars:],
            stderr=((exc.stderr or "") + f"\ncommand timed out after {timeout_s}s")[-max_output_chars:],
        )
    return BashResult(
        exit_code=completed.returncode,
        stdout=completed.stdout[-max_output_chars:],
        stderr=completed.stderr[-max_output_chars:],
    )


def truncate_conversation(
    messages: list[dict[str, Any]],
    *,
    max_context_tokens: int,
    target_fraction: float,
) -> list[dict[str, Any]]:
    if not messages or messages[0].get("role") != "system":
        raise ValueError("conversation must start with a system message")
    if _estimated_tokens(messages) <= max_context_tokens:
        return list(messages)
    target = max(1, int(max_context_tokens * target_fraction))
    remaining = list(messages)
    while len(remaining) > 1 and _estimated_tokens(remaining) > target:
        if (
            len(remaining) > 2
            and remaining[1].get("role") == "assistant"
            and remaining[2].get("role") == "tool"
        ):
            del remaining[1:3]
        else:
            del remaining[1]
    return remaining


def _estimated_tokens(messages: list[dict[str, Any]]) -> int:
    encoded = json.dumps(messages, ensure_ascii=True, separators=(",", ":"))
    return max(1, len(encoded) // 4)


def _assistant_tool_message(
    call: ToolCall,
    content: str,
    reasoning_content: str,
) -> dict[str, Any]:
    message = {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments, ensure_ascii=True),
                },
            }
        ],
    }
    if reasoning_content:
        message["reasoning_content"] = reasoning_content
    return message


def _assistant_text_message(
    content: str,
    reasoning_content: str,
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "role": "assistant",
        "content": content,
    }
    if reasoning_content:
        message["reasoning_content"] = reasoning_content
    return message


def _tool_message(call_id: str, result: BashResult) -> dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(
            {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
            ensure_ascii=True,
        ),
    }


def _backup_source_path(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    for src, dst in _iter_cp_pairs(parts):
        if src.startswith("/sandbox/etc/") and dst == f"{src}.maint-backup":
            return src
    return None


def _mutation_target_under_etc(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts:
        return None
    if parts[0] == "sed" and "-i" in parts and parts[-1].startswith("/sandbox/etc/"):
        return parts[-1]
    if parts[0] == "cat" and ">" in parts:
        index = parts.index(">")
        if index + 1 < len(parts) and parts[index + 1].startswith("/sandbox/etc/"):
            return parts[index + 1]
    if ">" in parts:
        index = parts.index(">")
        if index + 1 < len(parts) and parts[index + 1].startswith("/sandbox/etc/"):
            return parts[index + 1]
    if parts[0] == "mv" and len(parts) >= 3 and parts[-1].startswith("/sandbox/etc/"):
        return parts[-1]
    if parts[0] == "cp" and len(parts) >= 3 and parts[-1].startswith("/sandbox/etc/"):
        dst = parts[-1]
        src = parts[-2]
        if dst != f"{src}.maint-backup":
            return dst
    return None


def _missing_backup_warning(command: str, backed_up_paths: set[str]) -> str | None:
    target = _mutation_target_under_etc(command)
    if target is None:
        return None
    if target in backed_up_paths:
        return None
    return (
        "That mutation was not executed. Before editing a persistent file under /sandbox/etc/, "
        "create a maint-backup in this cycle with: "
        f"`cp --preserve=all -- {target} {target}.maint-backup`."
    )


def _is_restore_command(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    for src, dst in _iter_cp_pairs(parts):
        if src.endswith(".maint-backup") and dst.startswith("/sandbox/etc/"):
            return True
    return False


def _premature_restore_warning(command: str, last_result: BashResult | None) -> str | None:
    if not _is_restore_command(command):
        return None
    if last_result is not None and last_result.exit_code != 0:
        return None
    return (
        "That restore was not executed. Restore from `.maint-backup` only after a failed "
        "verification or failed restart in the immediately preceding step. If current checks are "
        "already passing, keep the backup and continue verification or finish with everything_ok."
    )


def _evidence_artifact_write_path(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if ">" not in parts:
        return None
    index = parts.index(">")
    if index + 1 >= len(parts):
        return None
    path = parts[index + 1]
    if not path.startswith("/sandbox/"):
        return None
    if not path.endswith(".maint-backup-list"):
        return None
    return path


def _evidence_overwrite_warning(command: str, evidence_artifacts_written: set[str]) -> str | None:
    path = _evidence_artifact_write_path(command)
    if path is None or path not in evidence_artifacts_written:
        return None
    return (
        "That command was not executed because it would overwrite an existing maintenance "
        f"evidence artifact `{path}`. Preserve previously captured evidence and continue with "
        "verification or remaining repairs."
    )


def _is_state_changing_command(command: str) -> bool:
    lowered = command.lower()
    if "> /sandbox/" in lowered:
        return True
    keywords = (
        "sed -i",
        "cat >",
        " mv ",
        " rm ",
        " find /sandbox/var/tmp",
        " systemctl restart ",
        "cp --preserve=all --",
    )
    return any(keyword in lowered for keyword in keywords)


def _forbidden_host_path_warning(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    blocked_prefixes = ("/etc/", "/var/", "/usr/")
    for part in parts:
        if not part.startswith("/"):
            continue
        if part.startswith("/sandbox/"):
            continue
        if part.startswith(blocked_prefixes):
            return (
                "That command was not executed. This harness permits file operations only under "
                "`/sandbox/...`. Replace host paths like `/etc/...`, `/var/...`, or `/usr/...` "
                "with the project's `/sandbox/...` paths from README and telemetry."
            )
    return None


def _forbidden_cd_sandbox_warning(command: str) -> str | None:
    lowered = command.lower()
    if lowered.startswith("cd /sandbox") or "&& cd /sandbox" in lowered or "cd /sandbox &&" in lowered:
        return (
            "That command was not executed. Do not `cd /sandbox` and switch to relative paths. "
            "Use absolute `/sandbox/...` paths exactly as written in README."
        )
    return None


def _temp_cache_backup_warning(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    for src, dst in _iter_cp_pairs(parts):
        if src.startswith("/sandbox/var/tmp/") and dst.endswith(".maint-backup"):
            return (
                "That command was not executed. Do not copy temporary cache files to `.maint-backup`. "
                "For temporary cache cleanup, preserve evidence by writing one backup list file "
                "(for example `find ... > ...maint-backup-list`) and then delete the cache files."
            )
    return None


def _iter_cp_pairs(parts: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    separators = {"&&", "||", ";"}
    index = 0
    while index < len(parts):
        if parts[index] != "cp":
            index += 1
            continue
        index += 1
        while index < len(parts) and parts[index].startswith("-"):
            index += 1
        if index + 1 >= len(parts):
            continue
        src = parts[index]
        if src in separators:
            continue
        dst = parts[index + 1]
        if dst in separators:
            continue
        pairs.append((src, dst))
        index += 2
    return pairs


def _terminal_command(command: str) -> tuple[str, str | None, str] | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts:
        return None
    terminal_name = _terminal_name(parts[0])
    if terminal_name in {"everything_ok", "yield"} and len(parts) == 1:
        return ("everything_ok", None, "")
    if terminal_name != "escalate":
        return None
    if len(parts) < 3:
        return None
    level = parts[1]
    message = " ".join(parts[2:]).strip()
    if level == "none":
        return ("escalate_none", "none", message)
    if level not in ESCALATION_LEVELS or not message:
        return None
    return ("escalate", level, message)


def _wrapped_terminal_control(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts or _terminal_name(parts[0]) not in {"echo", "printf", "bash", "sh", "sudo"}:
        return None
    for index, part in enumerate(parts[1:], start=1):
        terminal = _terminal_name(part)
        if terminal in {"everything_ok", "yield"}:
            return "everything_ok"
        if terminal == "escalate":
            return " ".join(parts[index:])
        if part.startswith("escalate "):
            return part
    return None


def _terminal_name(value: str) -> str:
    return Path(value).name


def _escalation_id(level: str | None, message: str) -> str:
    digest = hashlib.sha256(f"{level}:{message}".encode("utf-8")).hexdigest()[:12]
    return f"esc_{digest}"


def _telemetry_has_actionable_signals(telemetry: dict[str, Any]) -> bool:
    host_events = telemetry.get("host_events")
    if isinstance(host_events, list):
        for event in host_events:
            if isinstance(event, dict) and str(event.get("severity", "")).lower() in {"error", "critical"}:
                return True
    notable = telemetry.get("notable_processes")
    if isinstance(notable, list) and notable:
        return True
    services = telemetry.get("services")
    if not isinstance(services, list):
        return False
    unhealthy = {"failed", "degraded", "unhealthy"}
    for service in services:
        if not isinstance(service, dict):
            continue
        if str(service.get("state", "")).lower() in unhealthy:
            return True
        if str(service.get("health", "")).lower() in unhealthy:
            return True
        events = service.get("events")
        if isinstance(events, list):
            for event in events:
                if isinstance(event, dict) and str(event.get("severity", "")).lower() in {"error", "critical"}:
                    return True
    return False


def _read_required_text(path: Path, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"{label} must not be empty: {path}")
    return content
