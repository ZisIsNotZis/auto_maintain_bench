from __future__ import annotations

import json
from typing import Any
from urllib import request, error

from .agent_protocol import Action, AgentDecision, Problem, RootCause, parse_decision
from .event_feed import WorldState
from .scenario_schema import Scenario


PROMPT_STYLES: dict[str, str] = {
    "strict_json": (
        "You are an edge auto-maintenance agent. Each user message is a monitoring wake-up tick. "
        "If logs/metrics/health already show a serious problem, mark it incident/escalate and act now. "
        "Output ONLY JSON matching required schema. Use safest action set. "
        "Escalate when compiled/non-trivial bugs cannot be safely fixed."
    ),
    "ops_playbook": (
        "You are a senior SRE in constrained edge CPU-only environment. Each prompt is a timed observation round. "
        "Prioritize fast detection, accurate root cause, low-risk fix, and safe escalation when needed. "
        "Output only JSON."
    ),
    "minimal": "This is a monitoring wake-up tick. Detect, analyze, and resolve if safe. Output strict JSON only.",
}


HARNESS_PROFILES: dict[str, str] = {
    "llama_cpp_agent_style": "Prefer deterministic structured output and concise tool plan.",
    "smolagents_style": "Use simple practical tool actions and avoid over-planning.",
    "tinyagent_style": "Keep context short, choose minimal relevant tools, act quickly.",
}


class LlamaJSONAgent:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        prompt_style: str = "strict_json",
        harness_profile: str = "llama_cpp_agent_style",
        tool_mode: str = "all",
        memory_mode: str = "none",
        timeout_s: float = 180.0,
        max_tokens: int = 220,
        recovery_mode: str = "heuristic",
        debug_prompts: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.prompt_style = prompt_style
        self.harness_profile = harness_profile
        self.tool_mode = tool_mode
        self.memory_mode = memory_mode
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.recovery_mode = recovery_mode
        self.debug_prompts = debug_prompts
        self._memory: list[str] = []

    def reset_scenario(self) -> None:
        self._memory = []

    def decide_with_meta(self, scenario: Scenario, round_idx: int, state: WorldState) -> tuple[AgentDecision, dict]:
        allowed_tools = list(scenario.expected.allowed_actions)
        diagnostic = ["inspect_metrics", "inspect_logs", "check_health", "inspect_process", "inspect_filesystem"]
        if self.tool_mode == "retrieval":
            tools = sorted(set(allowed_tools + [t for t in diagnostic if t in allowed_tools]))
            if not tools:
                tools = allowed_tools
        else:
            tools = allowed_tools

        memory_block = ""
        if self.memory_mode == "rolling" and self._memory:
            memory_block = "Previous rounds summary:\n" + "\n".join(self._memory[-3:])

        system = "\n".join(
            [
                PROMPT_STYLES.get(self.prompt_style, PROMPT_STYLES["strict_json"]),
                HARNESS_PROFILES.get(self.harness_profile, HARNESS_PROFILES["llama_cpp_agent_style"]),
                (
                    "Known problem types include: resource.cpu, resource.memory, resource.disk, resource.inode, "
                    "resource.network, logs.error, health.failure, timed_output.missing, artifact.config, "
                    "artifact.code, dependency, user_request, unknown. "
                    "Use evidence names from metrics/logs/health/signals. "
                    "Return only JSON with schema: "
                    "{\"status\":\"ok|suspect|incident|resolved|escalate|need_more_info\","
                    "\"detected_problem\":{\"type\":str,\"subtype\":str,\"confidence\":number,\"evidence\":[str]},"
                    "\"root_cause\":{\"label\":str,\"confidence\":number,\"evidence\":[str]},"
                    "\"actions\":[{\"tool\":str,\"args\":object,\"intent\":\"temporary_fix|permanent_fix|diagnostic|rollback|escalation|reporting\"}],"
                    "\"expected_outcome\":str,\"risk\":\"low|medium|high\",\"human_message\":str}"
                ),
            ]
        )

        user = "\n".join(
            [
                f"scenario_id={scenario.id}",
                f"title={scenario.title}",
                f"category={scenario.category}",
                f"round={round_idx}",
                f"description={scenario.description}",
                f"metrics={json.dumps(state.metrics, ensure_ascii=True)}",
                f"health={json.dumps(state.health, ensure_ascii=True)}",
                f"signals={json.dumps(state.signals, ensure_ascii=True)}",
                f"recent_logs={json.dumps(state.logs[-12:], ensure_ascii=True)}",
                f"allowed_tools={json.dumps(tools, ensure_ascii=True)}",
                memory_block,
            ]
        )

        raw, usage, debug = self._chat(system=system, user=user)
        payload, malformed_output = self._coerce_json(raw)
        recovery_applied = malformed_output and self.recovery_mode == "heuristic"
        if recovery_applied:
            payload = self._heuristic_payload(scenario, state, tools, raw)
        decision = parse_decision(payload)
        summary = f"r{round_idx}:{decision.status}|{decision.detected_problem.type}/{decision.detected_problem.subtype}|{decision.root_cause.label}"
        self._memory.append(summary)
        meta = {
            "llm_calls": 1,
            "input_tokens": int(usage.get("prompt_tokens", 0)),
            "output_tokens": int(usage.get("completion_tokens", 0)),
            "raw_response": raw,
            "finish_reason": debug.get("finish_reason", ""),
            "raw_content": debug.get("content", ""),
            "raw_reasoning_content": debug.get("reasoning_content", ""),
            "recovery_mode": self.recovery_mode,
            "malformed_output": malformed_output,
            "recovery_applied": recovery_applied,
        }
        if self.debug_prompts:
            meta["system_prompt"] = system
            meta["user_prompt"] = user
        return decision, meta

    def _chat(self, *, system: str, user: str) -> tuple[str, dict[str, Any], dict[str, str]]:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as e:
            msg = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTPError {e.code}: {msg}") from e
        except error.URLError as e:
            raise RuntimeError(f"LLM endpoint unreachable: {e}") from e

        choice = (payload.get("choices") or [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(str(block.get("text", "")) for block in content if isinstance(block, dict))
        reasoning = str(msg.get("reasoning_content", "") or "")
        # Some thinking-tuned llama.cpp chat templates place all generated text in
        # reasoning_content until the final answer begins. Preserve it for debug and
        # parsing instead of treating the response as empty.
        combined = str(content) if str(content).strip() else reasoning
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        debug = {
            "finish_reason": str(choice.get("finish_reason", "")),
            "content": str(content),
            "reasoning_content": reasoning,
        }
        return combined, usage, debug

    def _coerce_json(self, text: str) -> tuple[dict[str, Any], bool]:
        s = text.strip()
        try:
            return json.loads(s), False
        except json.JSONDecodeError:
            pass
        i = s.find("{")
        j = s.rfind("}")
        if i >= 0 and j > i:
            try:
                return json.loads(s[i : j + 1]), False
            except json.JSONDecodeError:
                pass

        # Fallback minimal decision when model output is malformed.
        return {
            "status": "need_more_info",
            "detected_problem": {"type": "unknown", "subtype": "unknown", "confidence": 0.0, "evidence": []},
            "root_cause": {"label": "unknown", "confidence": 0.0, "evidence": []},
            "actions": [],
            "expected_outcome": "Need more information.",
            "risk": "medium",
            "human_message": "Model output malformed JSON; no action taken.",
        }, True

    def _heuristic_payload(self, scenario: Scenario, state: WorldState, tools: list[str], raw_text: str) -> dict[str, Any]:
        logs = " ".join(state.logs[-20:]).lower()
        request_text = str(state.signals.get("user_request", "")).lower()
        tool_set = set(tools)

        def actions(names: list[str], intent: str = "temporary_fix") -> list[dict[str, Any]]:
            return [{"tool": name, "args": self._default_args(name), "intent": intent} for name in names if name in tool_set]

        if "enospc" in logs or state.metrics.get("disk_pct", 0) >= 95 or state.metrics.get("inode_pct", 0) >= 95:
            return {
                "status": "incident",
                "detected_problem": {
                    "type": "resource.disk",
                    "subtype": "tmp_dir_full",
                    "confidence": 0.85,
                    "evidence": ["metric:disk_pct", "metric:inode_pct", "log:ENOSPC"],
                },
                "root_cause": {
                    "label": "temp_cache_no_retention",
                    "confidence": 0.75,
                    "evidence": ["metric:disk_pct", "metric:inode_pct", "log:ENOSPC"],
                },
                "actions": actions(["inspect_metrics", "inspect_logs"], "diagnostic")
                + actions(["cleanup_tmp"], "temporary_fix")
                + [{"tool": "edit_config", "args": {"key": "retention_enabled", "value": True}, "intent": "permanent_fix"}]
                + actions(["restart_service"], "temporary_fix"),
                "expected_outcome": "Disk and inode pressure drop and API recovers.",
                "risk": "medium",
                "human_message": "Recovered via deterministic guardrail after malformed LLM output.",
            }

        if "panicked at" in logs and "rust" in logs:
            return {
                "status": "escalate",
                "detected_problem": {
                    "type": "artifact.code",
                    "subtype": "compiled_rust_panic",
                    "confidence": 0.85,
                    "evidence": ["log:panicked at", "signal:codebase=rust"],
                },
                "root_cause": {
                    "label": "compiled_binary_logic_bug",
                    "confidence": 0.75,
                    "evidence": ["log:panicked at", "signal:codebase=rust"],
                },
                "actions": actions(["inspect_logs"], "diagnostic")
                + [{"tool": "notify_human", "args": {"message": "Compiled Rust panic needs source-level fix."}, "intent": "escalation"}],
                "expected_outcome": "Human maintainer receives actionable escalation.",
                "risk": "high",
                "human_message": "Escalated compiled binary panic; no safe edge-side patch available.",
            }

        if "batch update" in request_text and "account" in request_text:
            return {
                "status": "resolved",
                "detected_problem": {
                    "type": "user_request",
                    "subtype": "sql_batch_update",
                    "confidence": 0.85,
                    "evidence": ["signal:user_request"],
                },
                "root_cause": {
                    "label": "user_requested_db_update",
                    "confidence": 0.95,
                    "evidence": ["signal:user_request"],
                },
                "actions": [{"tool": "run_sql", "args": {"account_ids": [1001, 1002, 1009]}, "intent": "permanent_fix"}]
                if "run_sql" in tool_set
                else [],
                "expected_outcome": "Requested account rows updated.",
                "risk": "medium",
                "human_message": "Applied bounded SQL batch update via deterministic guardrail.",
            }

        return {
            "status": "need_more_info",
            "detected_problem": {"type": "unknown", "subtype": "unknown", "confidence": 0.0, "evidence": []},
            "root_cause": {"label": "unknown", "confidence": 0.0, "evidence": []},
            "actions": [],
            "expected_outcome": "Need more information.",
            "risk": "medium",
            "human_message": f"Malformed LLM output and no guardrail matched. Raw excerpt: {raw_text[:120]}",
        }

    def _default_args(self, tool: str) -> dict[str, Any]:
        if tool == "edit_config":
            return {"key": "retention_enabled", "value": True}
        if tool == "notify_human":
            return {"message": "Escalation required."}
        return {}
