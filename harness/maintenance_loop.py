from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
from typing import Any, Callable, Protocol
from urllib import error, request

from .rejections import load_rejection_rules, match_rejection
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
        self.rejection_rules = load_rejection_rules(
            Path(__file__).resolve().parent / "rejections"
        )

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
        require_terminal = False
        duplicate_attempts = 0
        consecutive_rereads = 0
        consecutive_parse_failures = 0
        consecutive_rejections = 0
        MAX_REJECTIONS = 3
        for _ in range(self.max_steps):
            if consecutive_rejections >= MAX_REJECTIONS:
                level = "uncertain" if state_changes > 0 else "failed"
                return WakeupResult(
                    terminal="escalate",
                    message="model_repeated_rejection_auto_escalated",
                    escalation_level=level,
                    escalation_id=_escalation_id(
                        level,
                        "model_repeated_rejection_auto_escalated",
                    ),
                    messages=tuple(audit_messages),
                    telemetry_path=telemetry_path,
                )
            consecutive_rejections += 1
            messages = truncate_conversation(
                messages,
                max_context_tokens=self.max_context_tokens,
                target_fraction=self.truncate_fraction,
            )
            response = self.transport.complete(
                messages=messages,
                tools=[self.bash_tool],
                tool_choice="auto",
            )
            content = str(response.get("content", "") or "").strip()
            reasoning_content = str(response.get("reasoning_content", "") or "")
            calls = response.get("tool_calls") or []

            # Check for terminal message in text content first (message protocol)
            terminal_msg = _terminal_message(content)
            if terminal_msg is not None:
                kind, level, message = terminal_msg
                if kind == "everything_ok" and telemetry_actionable and not executed_commands:
                    tel_dir = (
                        self.telemetry_display_dir
                        or str(self.telemetry_archive.root.resolve())
                    )
                    additions = [
                        _assistant_text_message(content, reasoning_content),
                        {
                            "role": "user",
                            "content": (
                                f"everything_ok rejected because actionable telemetry "
                                f"indicates unresolved issues. Check the latest telemetry "
                                f"at `{tel_dir}/latest.json` before calling everything_ok."
                            ),
                        },
                    ]
                    messages.extend(additions)
                    audit_messages.extend(additions)
                    continue
                return WakeupResult(
                    terminal=kind,
                    message=message,
                    escalation_level=level,
                    escalation_id=_escalation_id(level, message),
                    messages=tuple(audit_messages) + (
                        _assistant_text_message(content, reasoning_content),
                    ),
                    telemetry_path=telemetry_path,
                )

            # No terminal message — require a bash tool call
            if len(calls) != 1 or not isinstance(calls[0], ToolCall) or calls[0].name != "bash":
                consecutive_parse_failures += 1
                if consecutive_parse_failures >= 3:
                    level = "uncertain" if state_changes > 0 else "failed"
                    return WakeupResult(
                        terminal="escalate",
                        message="model_repeated_empty_responses_auto_escalated",
                        escalation_level=level,
                        escalation_id=_escalation_id(
                            level,
                            "model_repeated_empty_responses_auto_escalated",
                        ),
                        messages=tuple(audit_messages),
                        telemetry_path=telemetry_path,
                    )
                additions = [
                    _assistant_text_message(content, reasoning_content),
                    {
                        "role": "user",
                        "content": (
                            "Your previous response did not contain a bash tool call. "
                            "Call bash exactly once now. Use ordinary bash to inspect "
                            "or repair. When done, output a terminal message (everything_ok or delegate)."
                        ),
                    },
                ]
                messages.extend(additions)
                audit_messages.extend(additions)
                continue
            consecutive_parse_failures = 0
            call = calls[0]
            command = call.arguments.get("command")
            if not isinstance(command, str) or not command.strip():
                terminal_hint = (
                    "Call `everything_ok` now if the repair is verified and complete."
                    if executed_commands
                    else "Start with the first command from the README repair sequence."
                )
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(2, "", "command must be a non-empty string"),
                    ),
                    {
                        "role": "user",
                        "content": (
                            f"Your previous message contained an empty command. {terminal_hint}"
                        ),
                    },
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
                    and not executed_commands
                ):
                    tel_dir = (
                        self.telemetry_display_dir
                        or str(self.telemetry_archive.root.resolve())
                    )
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
                                "Do not call everything_ok yet without investigation. "
                                f"Check {tel_dir}/ for newer samples — "
                                "the issue may have resolved between collection ticks. "
                                "If the latest sample is still actionable, make a repair "
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
                # Model was told to terminate but tried a non-terminal command.
                # Auto-resolve: if changes were made, assume fix is complete.
                if state_changes > 0:
                    return WakeupResult(
                        terminal="everything_ok",
                        message="auto_everything_ok_after_terminal_required",
                        escalation_level="",
                        escalation_id="auto_everything_ok_after_terminal_required",
                        messages=tuple(audit_messages),
                        telemetry_path=telemetry_path,
                    )
                else:
                    return WakeupResult(
                        terminal="escalate",
                        message="auto_escalated_after_terminal_required",
                        escalation_level="failed",
                        escalation_id=_escalation_id(
                            "failed",
                            "auto_escalated_after_terminal_required",
                        ),
                        messages=tuple(audit_messages),
                        telemetry_path=telemetry_path,
                    )
            reread_warning = self._context_reread_warning(command)
            if reread_warning is not None:
                consecutive_rereads += 1
                if consecutive_rereads >= 3:
                    level = "uncertain" if state_changes > 0 else "failed"
                    return WakeupResult(
                        terminal="escalate",
                        message="model_repeated_reread_auto_escalated",
                        escalation_level=level,
                        escalation_id=_escalation_id(
                            level,
                            "model_repeated_reread_auto_escalated",
                        ),
                        messages=tuple(audit_messages),
                        telemetry_path=telemetry_path,
                    )
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
                if duplicate_attempts >= 5:
                    return WakeupResult(
                        terminal="escalate",
                        message="model_repeated_duplicate_commands_auto_escalated",
                        escalation_level="failed",
                        escalation_id=_escalation_id(
                            "failed",
                            "model_repeated_duplicate_commands_auto_escalated",
                        ),
                        messages=tuple(audit_messages),
                        telemetry_path=telemetry_path,
                    )
                warning = (
                    "That exact bash command was not executed because it already ran "
                    "during this maintenance cycle. The tool response repeats its cached "
                    "prior result. Do not call it again. Continue with the next literal "
                    "step from the README sequence, or if the sequence can no longer "
                    "proceed safely, verify existing evidence, then finish with "
                    "everything_ok or escalate."
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
            backup_target = _auto_backup_target(command, backed_up_paths)
            if backup_target is not None:
                backup_cmd = f"cp --preserve=all -- {shlex.quote(backup_target)} {shlex.quote(backup_target)}.maint-backup"
                subprocess.run(backup_cmd, shell=True, capture_output=True, timeout=10)
                backed_up_paths.add(backup_target)
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
            simple_rejection = match_rejection(command, self.rejection_rules)
            if simple_rejection is not None:
                additions = [
                    _assistant_tool_message(call, content, reasoning_content),
                    _tool_message(
                        call.id,
                        BashResult(
                            2,
                            "",
                            simple_rejection.stderr,
                        ),
                    ),
                    {
                        "role": "user",
                        "content": simple_rejection.user_message,
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
            consecutive_rejections = 0
            duplicate_attempts = 0
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
            additions = [
                _assistant_tool_message(call, content, reasoning_content),
                _tool_message(call.id, result),
            ]
            messages.extend(additions)
            audit_messages.extend(additions)
        return WakeupResult(
            terminal="escalate",
            message="model_exceeded_max_steps_without_terminal_command",
            escalation_level="uncertain" if state_changes > 0 else "failed",
            escalation_id=_escalation_id(
                "uncertain" if state_changes > 0 else "failed",
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
        highlights = self._extract_telemetry_highlights(telemetry)
        highlights_block = f"\n## Telemetry Highlights\n{highlights}\n" if highlights else ""
        return (
            f"# Project README\nSource: {readme_path}\n\n{readme}\n\n"
            "# Memory\n"
            f"Source: {memory_path}\n\n{memory or '(empty)'}\n\n"
            "# Current telemetry"
            f"{highlights_block}\n"
            f"{json.dumps(telemetry, ensure_ascii=True, indent=2, sort_keys=True)}"
        )

    @staticmethod
    def _extract_telemetry_highlights(telemetry: dict[str, Any]) -> str:
        """Extract a plain-text summary of the most important telemetry signals.

        This helps smaller models that struggle to parse deeply nested JSON.
        Formats:
          - Service health summary for every service
          - stdout+stderr from all services (operator requests, errors, diagnostics)
          - Critical/error/warning events (service + host)
          - Resource pressure signals (CPU, memory, filesystem, connectivity)
          - Request error rates > 10%
          - Notable outlier processes
        """
        lines: list[str] = []

        # Track which services need attention
        services = telemetry.get("services", [])
        host_mem_total = telemetry.get("memory", {}).get("total_bytes", 1)

        for svc in services:
            name = svc.get("name", "?")
            state = svc.get("state", "?")
            health = svc.get("health", "?")
            restart_count = svc.get("restart_count", 0)
            uptime_s = svc.get("uptime_s", 0)
            cpu_pct = svc.get("cpu_pct", 0)
            mem_bytes = svc.get("memory_bytes", 0)
            mem_pct = svc.get("memory_pct", round(100.0 * mem_bytes / host_mem_total, 1)) if mem_bytes else 0

            # Always show service header for any non-healthy service
            is_unhealthy = (state != "running" or health != "healthy" or restart_count > 0)
            if is_unhealthy:
                uptime_str = f"{uptime_s // 3600}h{(uptime_s % 3600) // 60}m" if uptime_s else "?"
                lines.append(f"- Service {name}: state={state} health={health} uptime={uptime_str} restart_count={restart_count} cpu={cpu_pct}% mem={mem_pct}%")

            # stdout lines (operator requests, startup messages, status)
            stdout = svc.get("stdout", {})
            for out_line in stdout.get("lines", []):
                text = out_line[:200]
                if is_unhealthy or any(kw in text.lower() for kw in ("operator request", "approved", "request:", "pending")):
                    lines.append(f"  stdout: {text}")

            # stderr lines (the most actionable diagnostic signals)
            stderr = svc.get("stderr", {})
            for err_line in stderr.get("lines", []):
                lines.append(f"  stderr: {err_line[:200]}")

            # Events (critical, error, warning)
            for event in svc.get("events", []):
                sev = event.get("severity", "")
                if sev in ("critical", "error", "warning"):
                    lines.append(f"  [{sev}] {event.get('code','?')}: {event.get('message','?')[:200]}")

            # Request metrics (if available)
            req = svc.get("requests")
            if isinstance(req, dict):
                err_pct = req.get("error_pct", 0)
                rate = req.get("rate_s", 0)
                lat_p50 = req.get("latency_p50_ms", 0)
                lat_p95 = req.get("latency_p95_ms", 0)
                inflight = req.get("inflight", 0)
                if err_pct > 10 or lat_p95 > 1000 or inflight > 10:
                    lines.append(f"  requests: {rate}/s errors={err_pct}% p50={lat_p50}ms p95={lat_p95}ms inflight={inflight}")

        # Host-level events
        for event in telemetry.get("host_events", []):
            sev = event.get("severity", "")
            if sev in ("critical", "error", "warning"):
                lines.append(f"- [host] [{sev}] {event.get('code','?')}: {event.get('message','?')[:200]}")

        # Connectivity
        conn = telemetry.get("connectivity", {})
        if conn.get("dns_resolution_ok") is False:
            lines.append("- connectivity: dns_resolution_ok=false")
        if conn.get("default_route_ok") is False:
            lines.append("- connectivity: default_route_ok=false")

        # Filesystem alerts (>80% warning, >=95% critical)
        for fs in telemetry.get("filesystems", []):
            used = fs.get("used_pct", 0)
            mount = fs.get("mount", "?")
            if used >= 95:
                lines.append(f"- filesystem {mount}: {used}% used (CRITICAL)")
            elif used >= 80:
                lines.append(f"- filesystem {mount}: {used}% used (warning)")

        # Memory alerts (>80% warning, >=90% critical)
        mem = telemetry.get("memory", {})
        used_pct = mem.get("used_pct", 0)
        if used_pct >= 90:
            lines.append(f"- memory: {used_pct}% used (CRITICAL)")
        elif used_pct >= 80:
            lines.append(f"- memory: {used_pct}% used (warning)")
        if mem.get("oom_kills_since_boot", 0) > 0:
            lines.append(f"- memory: {mem['oom_kills_since_boot']} OOM kills since boot")

        # CPU alerts (>80% warning, >=95% critical)
        cpu = telemetry.get("cpu", {})
        cpu_used = cpu.get("usage_pct", 0)
        if cpu_used >= 95:
            lines.append(f"- cpu: {cpu_used}% utilization (CRITICAL)")
        elif cpu_used >= 80:
            lines.append(f"- cpu: {cpu_used}% utilization (warning)")

        # Notable processes (all are significant)
        for proc in telemetry.get("notable_processes", []):
            pname = proc.get("name", "?")
            reasons = ", ".join(proc.get("reasons", []))
            cpu_p = proc.get("cpu_pct", 0)
            mem_b = proc.get("memory_bytes", 0)
            mem_mb = round(mem_b / 1048576, 1) if mem_b else 0
            lines.append(f"- notable process: {pname} cpu={cpu_p}% mem={mem_mb}MB reasons=[{reasons}]")

        # Escalating issues from prior cycles
        for esc in telemetry.get("escalating", []):
            lines.append(f"- escalating: {esc.get('message','?')[:200]}")

        return "\n".join(lines)

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


_BACKUP_SUFFIXES = (".maint-backup", ".backup", ".bak")


def _backup_source_path(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    for src, dst in _iter_cp_pairs(parts):
        if src.startswith("/sandbox/etc/") and any(
            dst == f"{src}{suffix}" for suffix in _BACKUP_SUFFIXES
        ):
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
    if parts[0] == "cat":
        for redirect in (">", ">>"):
            if redirect in parts:
                index = parts.index(redirect)
                if index + 1 < len(parts) and parts[index + 1].startswith("/sandbox/etc/"):
                    return parts[index + 1]
    # Generic redirect check (echo, printf, etc.)
    for redirect in (">", ">>"):
        if redirect in parts:
            index = parts.index(redirect)
            if (
                index + 1 < len(parts)
                and parts[index + 1].startswith("/sandbox/etc/")
            ):
                return parts[index + 1]
    if parts[0] == "mv" and len(parts) >= 3 and parts[-1].startswith("/sandbox/etc/"):
        return parts[-1]
    # Use _iter_cp_pairs to correctly identify cp src/dst pairs,
    # even when commands are chained with && / ||
    if parts[0] == "cp":
        for src, dst in _iter_cp_pairs(parts):
            if dst.startswith("/sandbox/etc/") and not any(dst == f"{src}{suffix}" for suffix in _BACKUP_SUFFIXES):
                return dst
        return None
    return None


def _auto_backup_target(command: str, backed_up_paths: set[str]) -> str | None:
    """Return the file path that needs auto-backup before mutation, or None."""
    target = _mutation_target_under_etc(command)
    if target is None:
        return None
    if target in backed_up_paths:
        return None
    return target


def _is_restore_command(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    for src, dst in _iter_cp_pairs(parts):
        if dst.startswith("/sandbox/etc/") and any(
            src.endswith(suffix) for suffix in _BACKUP_SUFFIXES
        ):
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


def _temp_cache_backup_warning(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    for src, dst in _iter_cp_pairs(parts):
        if src.startswith("/sandbox/var/tmp/") and any(
            dst.endswith(suffix) for suffix in _BACKUP_SUFFIXES
        ):
            return (
                "That command was not executed. Do not copy temporary cache files to a backup file. "
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


def _terminal_message(text: str) -> tuple[str, str | None, str] | None:
    """Parse a terminal signal from the model's text response (message protocol)."""
    if not text:
        return None
    stripped = text.strip()
    # everything_ok — must be exactly that, possibly with whitespace
    if stripped == "everything_ok":
        return ("everything_ok", None, "")
    # delegate <level> <message> — hand off to a human operator
    if stripped.startswith("delegate "):
        return _parse_delegate_terminal(stripped)
    return None


def _terminal_command(command: str) -> tuple[str, str | None, str] | None:
    """Detect terminal signals in bash commands.

    The model may terminate via:
    - bare 'everything_ok' or 'delegate <level> <message>' as a bash command
    - echo "everything_ok" or echo "delegate <level> <message>"
    """
    if not command:
        return None
    stripped = command.strip()
    # Strip surrounding quotes in case it's "everything_ok" or 'everything_ok'
    unquoted = stripped.strip("\"'")
    if unquoted == "everything_ok":
        return ("everything_ok", None, "")
    # echo everything_ok, echo "everything_ok", ECHO "everything_ok"
    lower = stripped.lower()
    if lower.startswith("echo "):
        echoed = stripped[5:].strip().strip("\"'")
        if echoed == "everything_ok":
            return ("everything_ok", None, "")
        if echoed.startswith("delegate "):
            return _parse_delegate_terminal(echoed)
    # Direct delegate command
    if stripped.startswith("delegate "):
        return _parse_delegate_terminal(stripped)
    return None


def _parse_delegate_terminal(text: str) -> tuple[str, str | None, str] | None:
    """Parse 'delegate <level> <message>' from text."""
    rest = text[len("delegate "):].strip()
    parts = rest.split(None, 1)
    if len(parts) >= 1:
        level = parts[0]
        message = parts[1] if len(parts) >= 2 else ""
        if level == "none":
            return ("escalate_none", "none", message)
        if level in ESCALATION_LEVELS and message:
            return ("escalate", level, message)
    return None


def _terminal_name(value: str) -> str:
    return Path(value).name


def _escalation_id(level: str | None, message: str) -> str:
    digest = hashlib.sha256(f"{level}:{message}".encode("utf-8")).hexdigest()[:12]
    return f"esc_{digest}"


def _slug(text: str, max_len: int = 40) -> str:
    """Slugify text for use in escalation message IDs."""
    slug = text.strip()[:max_len]
    slug = slug.replace(" ", "_")
    return slug


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
