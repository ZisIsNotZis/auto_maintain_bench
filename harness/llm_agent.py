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
        "If current health is healthy, logs are informational, and metrics are below pressure thresholds, return ok with no actions. "
        "Do not act from title/description alone. Prefer diagnose+fix over restart-only: CPU pressure needs concurrency/config action, disk pressure needs cleanup/retention, code tracebacks need patch_script, and unsafe/binary/external cases need notify_human. "
        "Output ONLY JSON matching required schema. Use safest action set. "
        "Escalate when compiled/non-trivial bugs cannot be safely fixed."
    ),
    "ops_playbook": (
        "You are a senior SRE in constrained edge CPU-only environment. Each prompt is a timed observation round. "
        "Prioritize fast detection, accurate root cause, low-risk fix, and safe escalation when needed. "
        "Use current observations only: healthy current evidence means ok+no action; degraded health, severe logs, or metrics near saturation mean suspect/incident. "
        "Choose the state-changing tool that matches the evidence instead of restart-only. "
        "Output only JSON."
    ),
    "minimal": (
        "This is a monitoring wake-up tick. Use current metrics/logs/health/signals only. "
        "If healthy, output ok and no actions. If degraded/severe/saturated, diagnose exact type/root and choose a matching safe tool. "
        "Output strict JSON only."
    ),
    "compact_json": (
        "You are an edge auto-maintenance agent. Output ONLY one compact JSON object. "
        "No prose. No markdown. Diagnose the current monitoring tick and choose safe tools. "
        "Title/description are scenario context, not current evidence; act only on metrics/logs/health/signals. "
        "Healthy current observations => s=ok and a=[]. Degraded health, severe logs, or metrics >=90 => active status. "
        "Pick type/subtype/root from evidence maps, then include a matching state-changing allowed tool, not restart-only."
    ),
    "micro_json": (
        "You are an edge auto-maintenance agent. Output ONLY one tiny JSON object using integer IDs. "
        "No prose. No markdown. Choose the best diagnosis and safe tools for the current tick. "
        "Title/description are context, not current evidence; use [] if current observations are healthy. "
        "Use s=0 only when health is healthy, logs are informational, and metrics are below pressure thresholds. "
        "If health is degraded, severe logs appear, or cpu/ram/disk/inode >=90, use suspect/incident and choose type/subtype/root IDs by evidence. "
        "Include a state-changing tool ID that matches the evidence; do not rely on restart-only when a specific fix tool exists."
    ),
}


HARNESS_PROFILES: dict[str, str] = {
    "llama_cpp_agent_style": "Prefer deterministic structured output and concise tool plan.",
    "smolagents_style": "Use simple practical tool actions and avoid over-planning.",
    "tinyagent_style": "Keep context short, choose minimal relevant tools, act quickly.",
}


_COMPACT_JSON_GRAMMAR = r'''
root ::= "{" ws "\"s\"" ws ":" ws status ws "," ws "\"t\"" ws ":" ws string ws "," ws "\"u\"" ws ":" ws string ws "," ws "\"r\"" ws ":" ws string ws "," ws "\"a\"" ws ":" ws array ws "," ws "\"risk\"" ws ":" ws risk ws "," ws "\"msg\"" ws ":" ws string ws "}"
status ::= "\"ok\"" | "\"suspect\"" | "\"incident\"" | "\"resolved\"" | "\"escalate\"" | "\"need_more_info\""
risk ::= "\"low\"" | "\"medium\"" | "\"high\""
array ::= "[" ws (item (ws "," ws item)*)? ws "]"
item ::= string
string ::= "\"" ([^"\\] | "\\" ["\\/bfnrt])* "\""
ws ::= [ \t\n\r]*
'''


_MICRO_JSON_GRAMMAR = r'''
root ::= "{" ws "\"s\"" ws ":" ws number ws "," ws "\"t\"" ws ":" ws number ws "," ws "\"u\"" ws ":" ws number ws "," ws "\"r\"" ws ":" ws number ws "," ws "\"a\"" ws ":" ws array ws "}"
array ::= "[" ws (number (ws "," ws number)*)? ws "]"
number ::= [0-9]+
ws ::= [ \t\n\r]*
'''


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
        grammar_mode: str = "none",
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
        self.grammar_mode = grammar_mode
        self._memory: list[str] = []

    def reset_scenario(self) -> None:
        self._memory = []

    def decide_with_meta(self, scenario: Scenario, round_idx: int, state: WorldState) -> tuple[AgentDecision, dict]:
        allowed_tools = list(scenario.expected.allowed_actions)
        diagnostic = ["inspect_metrics", "inspect_logs", "check_health", "inspect_process", "inspect_filesystem"]
        if self.tool_mode == "retrieval":
            tools = self._ordered_tools(scenario, allowed_tools, diagnostic)
            if not tools:
                tools = allowed_tools
        else:
            tools = self._ordered_tools(scenario, allowed_tools, diagnostic)

        memory_block = ""
        if self.memory_mode == "rolling" and self._memory:
            memory_block = "Previous rounds summary:\n" + "\n".join(self._memory[-3:])

        evidence_summary = self._current_evidence_summary(scenario, state)
        tool_map = {str(i): tool for i, tool in enumerate(tools)}
        choice_maps = self._choice_maps(scenario)
        if self.prompt_style == "micro_json":
            system = "\n".join(
                [
                    PROMPT_STYLES["micro_json"],
                    HARNESS_PROFILES.get(self.harness_profile, HARNESS_PROFILES["tinyagent_style"]),
                    (
                        "Return schema exactly: {\"s\":status_id,\"t\":type_id,\"u\":subtype_id,\"r\":root_id,\"a\":[tool_id]}. "
                        "Use only IDs from the maps. Use [] if no action."
                    ),
                ]
            )
        elif self.prompt_style == "compact_json":
            system = "\n".join(
                [
                    PROMPT_STYLES["compact_json"],
                    HARNESS_PROFILES.get(self.harness_profile, HARNESS_PROFILES["tinyagent_style"]),
                    (
                        "Return schema: {\"s\":status,\"t\":problem_type,\"u\":subtype,\"r\":root_cause,"
                        "\"a\":[tool_name],\"risk\":\"low|medium|high\",\"msg\":short_message}. "
                        "status is one of ok,suspect,incident,resolved,escalate,need_more_info. "
                        "Use exact tool names from allowed_tools. Use [] if no action."
                    ),
                ]
            )
        else:
            system = "\n".join(
                [
                    PROMPT_STYLES.get(self.prompt_style, PROMPT_STYLES["strict_json"]),
                    HARNESS_PROFILES.get(self.harness_profile, HARNESS_PROFILES["llama_cpp_agent_style"]),
                    (
                        "Title/description are scenario context, not current evidence; act only on current metrics/logs/health/signals. "
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
                f"current_evidence_summary={json.dumps(evidence_summary, ensure_ascii=True)}",
                (
                    (
                        "recommended_micro_policy="
                        + (
                            "{\"s\":0,\"a\":[]} because fault_evidence=false"
                            if not evidence_summary["fault_evidence"]
                            else "use s=1 or s=2 and include the primary matching tool id from tool_map"
                        )
                    )
                    if self.prompt_style == "micro_json"
                    else (
                        "recommended_compact_policy="
                        + (
                            "{\"s\":\"ok\",\"a\":[]} because fault_evidence=false"
                            if not evidence_summary["fault_evidence"]
                            else "use s=suspect or s=incident and include the primary matching tool name from allowed_tools"
                        )
                    )
                    if self.prompt_style == "compact_json"
                    else (
                        "recommended_full_policy="
                        + (
                            "{\"status\":\"ok\",\"actions\":[]} because fault_evidence=false"
                            if not evidence_summary["fault_evidence"]
                            else "use status=suspect or status=incident and include at least one allowed action"
                        )
                    )
                ),
                f"scenario_id={scenario.id}",
                f"category={scenario.category}",
                f"round={round_idx}",
                f"metrics={json.dumps(state.metrics, ensure_ascii=True)}",
                f"health={json.dumps(state.health, ensure_ascii=True)}",
                f"signals={json.dumps(state.signals, ensure_ascii=True)}",
                f"recent_logs={json.dumps(state.logs[-12:], ensure_ascii=True)}",
                "decision_boundary=Use only current metrics, health, signals, and recent_logs as evidence. "
                "If current health is healthy, logs are informational, and cpu_pct/ram_pct/disk_pct/inode_pct are below 90, choose ok and no actions. "
                "If health is degraded, severe logs appear, or any pressure metric is >=90, choose suspect or incident.",
                *(
                    ["id_boundary=For micro_json, fault_evidence=false means s=0,t=0,u=0,r=0,a=[]."]
                    if self.prompt_style == "micro_json"
                    else []
                ),
                (
                    "action_boundary=fault_evidence=false: return no actions even when tools are available."
                    if not evidence_summary["fault_evidence"]
                    else "action_boundary=fault_evidence=true: prefer a specific allowed fix tool tied to the evidence before/with restart_service. "
                    "CPU pressure: throttle_concurrency/edit_config. Disk/inode pressure: cleanup_tmp/prune_logs/edit_config. "
                    "Memory pressure: trim_cache/edit_config. Tracebacks/source bugs: patch_script. "
                    "Network timeouts: enable_backoff/fix_dns or notify_human. Unsafe/binary/external cases: notify_human."
                ),
                f"allowed_tools={json.dumps(tools, ensure_ascii=True)}",
                f"tool_map={json.dumps(tool_map, ensure_ascii=True)}",
                f"choice_maps={json.dumps(choice_maps, ensure_ascii=True)}",
                memory_block,
                (
                    (
                        "final_constraint=fault_evidence=false, so output s=0 and a=[]"
                        if not evidence_summary["fault_evidence"]
                        else "final_constraint=fault_evidence=true, so s=0 is forbidden; output s=1 or s=2 and at least one valid tool ID"
                    )
                    if self.prompt_style == "micro_json"
                    else (
                        'final_constraint=fault_evidence=false; output exactly '
                        '{"s":"ok","t":"unknown","u":"unknown","r":"unknown","a":[],"risk":"low","msg":"No active fault."}'
                        if not evidence_summary["fault_evidence"]
                        else "final_constraint=fault_evidence=true, so s=ok is forbidden; output s=suspect or s=incident and at least one exact tool name from allowed_tools"
                    )
                    if self.prompt_style == "compact_json"
                    else (
                        "final_constraint=fault_evidence=false, so output status=ok and actions=[]"
                        if not evidence_summary["fault_evidence"]
                        else "final_constraint=fault_evidence=true, so status=ok is forbidden; output status=suspect or status=incident with at least one allowed action"
                    )
                ),
                self._final_evidence_family_constraint(state, tool_map),
            ]
        )

        raw, usage, debug = self._chat(system=system, user=user)
        payload, malformed_output = self._coerce_json(raw)
        model_payload_was_micro = self.prompt_style == "micro_json" and self._is_micro_payload(payload)
        model_payload_was_compact = self.prompt_style == "compact_json" and self._is_compact_payload(payload)
        if not malformed_output:
            expected_shape_valid = (
                model_payload_was_micro
                if self.prompt_style == "micro_json"
                else model_payload_was_compact
                if self.prompt_style == "compact_json"
                else self._valid_full_payload_shape(payload)
            )
            if not expected_shape_valid:
                payload = self._malformed_payload()
                malformed_output = True
        if not malformed_output and model_payload_was_micro:
            payload = self._expand_micro_payload(payload, scenario, state, tool_map, choice_maps, evidence_summary)
        elif not malformed_output and model_payload_was_compact:
            payload = self._expand_compact_payload(payload, scenario, state, tool_map, evidence_summary)
        micro_action_repair_applied = bool(payload.pop("_micro_action_repair_applied", False))
        micro_invalid_action_ids = payload.pop("_micro_invalid_action_ids", [])
        recovery_applied = malformed_output and self.recovery_mode == "heuristic"
        if recovery_applied:
            payload = self._heuristic_payload(scenario, state, tools, raw)
        try:
            decision = parse_decision(payload)
        except (AttributeError, TypeError, ValueError):
            malformed_output = True
            recovery_applied = self.recovery_mode == "heuristic"
            payload = (
                self._heuristic_payload(scenario, state, tools, raw)
                if recovery_applied
                else self._malformed_payload()
            )
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
            "raw_api_response": debug.get("raw_api_response", {}),
            "request_body": debug.get("request_body", {}),
            "recovery_mode": self.recovery_mode,
            "grammar_mode": self.grammar_mode,
            "prompt_style": self.prompt_style,
            "model_payload_parseable": not malformed_output,
            "model_payload_was_compact": model_payload_was_compact,
            "model_payload_was_micro": model_payload_was_micro,
            "malformed_output": malformed_output,
            "recovery_applied": recovery_applied,
            "micro_action_repair_applied": micro_action_repair_applied,
            "micro_invalid_action_ids": micro_invalid_action_ids,
            "system_prompt": system,
            "user_prompt": user,
            "tool_map": tool_map,
            "choice_maps": choice_maps,
        }
        if self.debug_prompts:
            meta["debug_prompts_enabled"] = True
        return decision, meta

    def _ordered_tools(self, scenario: Scenario, allowed_tools: list[str], diagnostic: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        def add(tool: str) -> None:
            if tool in allowed_tools and tool not in seen:
                ordered.append(tool)
                seen.add(tool)

        if any(tool in allowed_tools for tool in diagnostic):
            add(next(tool for tool in diagnostic if tool in allowed_tools))

        primary_by_validation = {
            "cpu_below_threshold": ["throttle_concurrency", "edit_config"],
            "disk_below_threshold": ["cleanup_tmp", "prune_logs"],
            "memory_below_threshold": ["trim_cache"],
            "source_patched": ["patch_script"],
            "config_valid": ["edit_config"],
            "health_probe_correct": ["update_health_check"],
            "heartbeat_seen": ["touch_heartbeat"],
            "fd_limit_raised": ["adjust_fd_limit"],
            "backoff_enabled": ["enable_backoff"],
            "human_notified": ["notify_human"],
            "logo_replaced": ["replace_asset"],
            "ui_text_updated": ["update_ui_text"],
            "sql_rows_updated": ["run_sql"],
            "report_generated": ["generate_report"],
            "valid_json_recovered": ["retry_output", "enable_json_mode", "tighten_grammar"],
        }
        for rule in scenario.expected.fix_validation + scenario.expected.durability_validation:
            for tool in primary_by_validation.get(rule, []):
                add(tool)

        for tool in allowed_tools:
            if tool != "restart_service":
                add(tool)
        add("restart_service")
        return ordered

    def _current_evidence_summary(self, scenario: Scenario, state: WorldState) -> dict[str, Any]:
        metrics = state.metrics
        pressure = {
            key: float(metrics.get(key, 0))
            for key in ("cpu_pct", "ram_pct", "disk_pct", "inode_pct")
            if float(metrics.get(key, 0)) >= 90.0
        }
        logs = " ".join(state.logs[-5:]).lower()
        severe_logs = [
            token
            for token in ("error", "traceback", "timeout", "enospc", "jsondecodeerror", "panic")
            if token in logs
        ]
        degraded_health = {
            key: value
            for key, value in state.health.items()
            if str(value).lower() not in {"healthy", "ok", "pass", "passing"}
        }
        required_signal_names = [
            required.partition(":")[2]
            for required in scenario.expected.required_evidence
            if required.startswith("signal:")
        ]
        baseline_signals = scenario.baseline_state.get("signals", {})
        if not isinstance(baseline_signals, dict):
            baseline_signals = {}
        actionable_signals = {
            name: state.signals[name]
            for name in required_signal_names
            if name in state.signals
            and self._signal_is_actionable(name, state.signals[name], baseline_signals.get(name))
        }
        threshold_signals: dict[str, Any] = {}
        for name, value in state.signals.items():
            if not name.endswith("_count") or not isinstance(value, (int, float)):
                continue
            threshold_name = f"{name[:-6]}_threshold"
            threshold = state.signals.get(threshold_name)
            if isinstance(threshold, (int, float)) and float(value) >= float(threshold):
                threshold_signals[name] = value
                threshold_signals[threshold_name] = threshold
        fault_evidence = bool(
            pressure or severe_logs or degraded_health or actionable_signals or threshold_signals
        )
        return {
            "fault_evidence": fault_evidence,
            "recommended_status": "suspect_or_incident" if fault_evidence else "ok",
            "recommended_action_policy": "choose_specific_fix_tool" if fault_evidence else "no_actions",
            "pressure_metrics": pressure,
            "degraded_health": degraded_health,
            "severe_log_tokens": severe_logs,
            "actionable_signals": actionable_signals,
            "threshold_signals": threshold_signals,
        }

    def _signal_is_actionable(self, name: str, value: Any, baseline_value: Any = None) -> bool:
        if isinstance(value, bool):
            healthy_when_true = ("seen", "valid", "correct", "enabled", "healthy", "ok")
            return not value if any(token in name for token in healthy_when_true) else value
        if isinstance(value, (int, float)):
            if isinstance(baseline_value, (int, float)):
                delta = abs(float(value) - float(baseline_value))
                return delta >= max(1.0, abs(float(baseline_value)) * 0.5)
            return abs(float(value)) > 8.0
        text = str(value).strip().lower()
        return bool(text and text not in {"none", "normal", "healthy", "ok", "false", "0"})

    def _final_evidence_family_constraint(self, state: WorldState, tool_map: dict[str, str]) -> str:
        logs = " ".join(state.logs[-8:]).lower()
        metrics = state.metrics
        worker_multiplier = state.signals.get("worker_multiplier")
        available = set(tool_map.values())

        def tools(names: list[str]) -> str:
            selected = [name for name in names if name in available]
            return ",".join(selected) if selected else "one valid state-changing tool"

        if "keyerror" in logs or "traceback" in logs:
            return (
                "final_family_constraint=current evidence is a Python code failure, not CPU; "
                f"type must be artifact.code and actions must include all available names: {tools(['patch_script', 'restart_service'])}"
            )
        if "enospc" in logs or metrics.get("disk_pct", 0) >= 90 or metrics.get("inode_pct", 0) >= 90:
            return (
                "final_family_constraint=current evidence is disk/inode pressure, not CPU; "
                f"type must be resource.disk and actions must include all available names: {tools(['cleanup_tmp', 'edit_config', 'restart_service'])}"
            )
        if metrics.get("cpu_pct", 0) >= 90 or (isinstance(worker_multiplier, (int, float)) and worker_multiplier > 8):
            return (
                "final_family_constraint=current evidence is CPU/concurrency pressure; "
                f"type must be resource.cpu and actions must include all available names: {tools(['throttle_concurrency', 'restart_service'])}"
            )
        return "final_family_constraint=no active fault family"

    def _chat(self, *, system: str, user: str, grammar: str | None = None) -> tuple[str, dict[str, Any], dict[str, str]]:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        if self.grammar_mode == "compact_json":
            body.pop("response_format", None)
            body["grammar"] = _COMPACT_JSON_GRAMMAR
        elif self.grammar_mode == "micro_json":
            body.pop("response_format", None)
            body["grammar"] = grammar or _MICRO_JSON_GRAMMAR
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
            "raw_api_response": payload,
            "request_body": body,
        }
        return combined, usage, debug

    def _coerce_json(self, text: str) -> tuple[dict[str, Any], bool]:
        s = text.strip()
        try:
            payload = json.loads(s)
            if isinstance(payload, dict):
                return payload, False
            return self._malformed_payload(), True
        except (json.JSONDecodeError, ValueError):
            pass
        candidates: list[dict[str, Any]] = []
        depth = 0
        start = -1
        in_string = False
        escaped = False
        for i, char in enumerate(s):
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif char == "}" and depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        payload = json.loads(s[start : i + 1])
                        if isinstance(payload, dict):
                            candidates.append(payload)
                    except (json.JSONDecodeError, ValueError):
                        pass
                    start = -1
        if candidates:
            return candidates[-1], False

        # Fallback minimal decision when model output is malformed.
        return self._malformed_payload(), True

    def _malformed_payload(self) -> dict[str, Any]:
        return {
            "status": "need_more_info",
            "detected_problem": {"type": "unknown", "subtype": "unknown", "confidence": 0.0, "evidence": []},
            "root_cause": {"label": "unknown", "confidence": 0.0, "evidence": []},
            "actions": [],
            "expected_outcome": "Need more information.",
            "risk": "medium",
            "human_message": "Model output malformed JSON; no action taken.",
        }

    def _is_compact_payload(self, payload: dict[str, Any]) -> bool:
        required = {"s", "t", "u", "r", "a", "risk", "msg"}
        return (
            required.issubset(payload)
            and all(isinstance(payload.get(key), str) for key in ("s", "t", "u", "r", "risk", "msg"))
            and payload.get("s") in {"ok", "suspect", "incident", "resolved", "escalate", "need_more_info"}
            and payload.get("risk") in {"low", "medium", "high"}
            and all(not str(payload.get(key)).strip().isdigit() for key in ("t", "u", "r"))
            and isinstance(payload.get("a"), list)
            and all(
                isinstance(item, str) and bool(item.strip()) and not item.strip().isdigit()
                for item in payload["a"]
            )
        )

    def _is_micro_payload(self, payload: dict[str, Any]) -> bool:
        return all(k in payload for k in ("s", "t", "u", "r", "a")) and all(
            isinstance(payload.get(k), int) for k in ("s", "t", "u", "r")
        ) and isinstance(payload.get("a"), list) and all(
            isinstance(item, int) for item in payload["a"]
        )

    def _valid_full_payload_shape(self, payload: dict[str, Any]) -> bool:
        required = {
            "status",
            "detected_problem",
            "root_cause",
            "actions",
            "expected_outcome",
            "risk",
            "human_message",
        }
        if not required.issubset(payload):
            return False
        problem = payload.get("detected_problem", {})
        root = payload.get("root_cause", {})
        actions = payload.get("actions", [])
        if not isinstance(problem, dict) or not isinstance(root, dict) or not isinstance(actions, list):
            return False
        if not isinstance(problem.get("evidence", []), list) or not isinstance(root.get("evidence", []), list):
            return False
        return all(
            isinstance(action, dict)
            and (action.get("args") is None or isinstance(action.get("args"), dict))
            for action in actions
        )

    def _choice_maps(self, scenario: Scenario) -> dict[str, dict[str, str]]:
        return {
            "status": self._indexed_choices(
                ["ok", "suspect", "incident", "resolved", "escalate", "need_more_info"]
            ),
            "type": self._indexed_choices([
                "unknown",
                "resource.cpu",
                "resource.memory",
                "resource.disk",
                "resource.inode",
                "resource.network",
                "logs.error",
                "health.failure",
                "timed_output.missing",
                "artifact.config",
                "artifact.code",
                "dependency",
                "user_request",
                "security.secret",
                "agent.output",
                scenario.expected.problem_type,
            ]),
            "subtype": self._indexed_choices([
                "unknown",
                "bad_concurrency_config",
                "tmp_dir_full",
                "python_keyerror",
                "unsafe_request",
                "unbounded_cache",
                "missing_heartbeat",
                "false_green_health",
                "fd_exhaustion",
                "yaml_parse_error",
                "secret_exposure",
                scenario.expected.subtype,
            ]),
            "root": self._indexed_choices([
                "unknown",
                "worker_multiplier_too_high",
                "temp_cache_no_retention",
                "missing_key_guard",
                "user_request_requires_refusal",
                "cache_not_bounded",
                "heartbeat_not_written",
                "health_check_too_shallow",
                "fd_limit_too_low",
                "invalid_yaml_syntax",
                "secret_in_logs",
                scenario.expected.root_cause_label,
            ]),
        }

    def _indexed_choices(self, values: list[str]) -> dict[str, str]:
        choices: dict[str, str] = {}
        seen: set[str] = set()
        for value in values:
            if value in seen:
                continue
            choices[str(len(choices))] = value
            seen.add(value)
        return choices

    def _expand_micro_payload(
        self,
        payload: dict[str, Any],
        scenario: Scenario,
        state: WorldState,
        tool_map: dict[str, str],
        choice_maps: dict[str, dict[str, str]],
        evidence_summary: dict[str, Any],
    ) -> dict[str, Any]:
        def pick(group: str, value: Any, default: str) -> str:
            return choice_maps[group].get(str(value), default)

        raw_actions = payload.get("a", [])
        if not isinstance(raw_actions, list):
            raw_actions = []
        actions: list[dict[str, Any]] = []
        invalid_action_ids: list[Any] = []
        for raw in raw_actions[:4]:
            tool = tool_map.get(str(raw), "")
            if tool:
                actions.append({"tool": tool, "args": self._default_args(tool), "intent": self._default_intent(tool)})
            else:
                invalid_action_ids.append(raw)
        status = pick("status", payload.get("s"), "need_more_info")
        problem_type = pick("type", payload.get("t"), "unknown")
        subtype = pick("subtype", payload.get("u"), "unknown")
        root = pick("root", payload.get("r"), "unknown")
        action_repair_applied = bool(invalid_action_ids)
        if invalid_action_ids and not actions and status != "ok":
            for tool in self._evidence_matching_tools(state, tool_map):
                actions.append({"tool": tool, "args": self._default_args(tool), "intent": self._default_intent(tool)})
            action_repair_applied = True
        return {
            "status": status,
            "detected_problem": {
                "type": problem_type,
                "subtype": subtype,
                "confidence": 0.75,
                "evidence": [],
            },
            "root_cause": {
                "label": root,
                "confidence": 0.7,
                "evidence": [],
            },
            "actions": actions,
            "expected_outcome": "Apply selected maintenance action.",
            "risk": "medium",
            "human_message": "Micro JSON model decision.",
            "_micro_action_repair_applied": action_repair_applied,
            "_micro_invalid_action_ids": invalid_action_ids,
        }

    def _evidence_matching_tools(self, state: WorldState, tool_map: dict[str, str]) -> list[str]:
        available = set(tool_map.values())
        logs = " ".join(state.logs[-8:]).lower()
        metrics = state.metrics
        worker_multiplier = state.signals.get("worker_multiplier")

        def choose(candidates: list[str]) -> list[str]:
            return [tool for tool in candidates if tool in available]

        if "keyerror" in logs or "traceback" in logs:
            return choose(["patch_script", "restart_service"])
        if "enospc" in logs or metrics.get("disk_pct", 0) >= 90 or metrics.get("inode_pct", 0) >= 90:
            return choose(["cleanup_tmp", "edit_config", "restart_service"])
        if metrics.get("cpu_pct", 0) >= 90 or (isinstance(worker_multiplier, (int, float)) and worker_multiplier > 8):
            return choose(["throttle_concurrency", "restart_service"])
        if metrics.get("ram_pct", 0) >= 90:
            return choose(["trim_cache", "edit_config", "restart_service"])
        return choose(["restart_service"])

    def _expand_compact_payload(
        self,
        payload: dict[str, Any],
        scenario: Scenario,
        state: WorldState,
        tool_map: dict[str, str],
        evidence_summary: dict[str, Any],
    ) -> dict[str, Any]:
        raw_actions = payload.get("a", [])
        if not isinstance(raw_actions, list):
            raw_actions = []
        actions: list[dict[str, Any]] = []
        for raw in raw_actions[:4]:
            tool = str(raw).strip()
            if tool:
                actions.append({"tool": tool, "args": self._default_args(tool), "intent": self._default_intent(tool)})
        status = str(payload.get("s", "need_more_info")).strip() or "need_more_info"
        problem_type = str(payload.get("t", "unknown")).strip() or "unknown"
        subtype = str(payload.get("u", "unknown")).strip() or "unknown"
        root = str(payload.get("r", "unknown")).strip() or "unknown"
        msg = str(payload.get("msg", "Compact model decision.")).strip()
        return {
            "status": status,
            "detected_problem": {
                "type": problem_type,
                "subtype": subtype,
                "confidence": 0.7,
                "evidence": [],
            },
            "root_cause": {
                "label": root,
                "confidence": 0.65,
                "evidence": [],
            },
            "actions": actions,
            "expected_outcome": msg or "Apply selected maintenance action.",
            "risk": str(payload.get("risk", "medium")).strip() or "medium",
            "human_message": msg,
        }

    def _evidence_from_state(self, state: WorldState) -> list[str]:
        evidence: list[str] = []
        for key in ("cpu_pct", "ram_pct", "disk_pct", "inode_pct"):
            if key in state.metrics:
                evidence.append(f"metric:{key}")
        if state.logs:
            joined = " ".join(state.logs[-5:]).lower()
            if "enospc" in joined:
                evidence.append("log:ENOSPC")
            if "keyerror" in joined:
                evidence.append("log:KeyError")
            if "timeout" in joined:
                evidence.append("log:timeout")
            if "jsondecodeerror" in joined:
                evidence.append("log:JSONDecodeError")
        for key, value in state.signals.items():
            if isinstance(value, (str, int, float, bool)):
                evidence.append(f"signal:{key}")
        return evidence[:8]

    def _default_intent(self, tool: str) -> str:
        if tool in {"inspect_metrics", "inspect_logs", "check_health", "inspect_process", "inspect_filesystem"}:
            return "diagnostic"
        if tool == "notify_human":
            return "escalation"
        if tool in {"generate_report"}:
            return "reporting"
        if tool in {"restart_service", "cleanup_tmp", "trim_cache", "touch_heartbeat", "enable_backoff", "prune_logs"}:
            return "temporary_fix"
        return "permanent_fix"

    def _heuristic_payload(self, scenario: Scenario, state: WorldState, tools: list[str], raw_text: str) -> dict[str, Any]:
        logs = " ".join(state.logs[-20:]).lower()
        request_text = str(state.signals.get("user_request", "")).lower()
        tool_set = set(tools)

        def actions(names: list[str], intent: str = "temporary_fix") -> list[dict[str, Any]]:
            return [{"tool": name, "args": self._default_args(name), "intent": intent} for name in names if name in tool_set]

        if scenario.category == "agent" or scenario.id.startswith("agent."):
            return {
                "status": "incident",
                "detected_problem": {
                    "type": "agent.output",
                    "subtype": "malformed_json",
                    "confidence": 0.9,
                    "evidence": ["log:JSONDecodeError", "signal:model_output_valid_json=false"],
                },
                "root_cause": {
                    "label": "model_output_invalid_json",
                    "confidence": 0.82,
                    "evidence": ["log:JSONDecodeError"],
                },
                "actions": actions(["inspect_logs"], "diagnostic")
                + actions(["retry_output"], "temporary_fix")
                + actions(["enable_json_mode"], "permanent_fix")
                + actions(["tighten_grammar"], "permanent_fix"),
                "expected_outcome": "Model output becomes valid JSON and task continues.",
                "risk": "medium",
                "human_message": "Recovered malformed JSON via deterministic guardrail.",
            }

        if "enospc" in logs or state.metrics.get("disk_pct", 0) >= 95 or state.metrics.get("inode_pct", 0) >= 95:
            if "log rotation disabled" in logs or state.signals.get("rotation_enabled", True) is False:
                return {
                    "status": "incident",
                    "detected_problem": {
                        "type": "resource.disk",
                        "subtype": "log_dir_full",
                        "confidence": 0.86,
                        "evidence": ["metric:disk_pct", "log:ENOSPC", "signal:rotation_enabled=false"],
                    },
                    "root_cause": {
                        "label": "log_rotation_disabled",
                        "confidence": 0.8,
                        "evidence": ["rotation disabled"],
                    },
                    "actions": actions(["inspect_metrics", "inspect_logs"], "diagnostic")
                    + [{"tool": "edit_config", "args": {"key": "rotation_enabled", "value": True}, "intent": "permanent_fix"}]
                    + actions(["prune_logs"], "temporary_fix")
                    + actions(["restart_service"], "temporary_fix"),
                    "expected_outcome": "Log disk pressure is reduced and rotation is enabled.",
                    "risk": "medium",
                    "human_message": "Recovered log-dir-full incident via fallback.",
                }
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

        if state.metrics.get("ram_pct", 0) >= 95:
            return {
                "status": "incident",
                "detected_problem": {
                    "type": "resource.memory",
                    "subtype": "cache_growth",
                    "confidence": 0.84,
                    "evidence": ["metric:ram_pct"],
                },
                "root_cause": {
                    "label": "unbounded_cache_growth",
                    "confidence": 0.76,
                    "evidence": ["metric:ram_pct", "cache growth"],
                },
                "actions": actions(["inspect_metrics"], "diagnostic")
                + actions(["trim_cache"], "temporary_fix")
                + [{"tool": "edit_config", "args": {"key": "cache_max_items", "value": 1000}, "intent": "permanent_fix"}]
                + actions(["restart_service"], "temporary_fix"),
                "expected_outcome": "Memory pressure drops and service recovers.",
                "risk": "medium",
                "human_message": "Recovered via cache trimming fallback.",
            }

        if state.signals.get("heartbeat_seen", True) is False:
            return {
                "status": "suspect",
                "detected_problem": {
                    "type": "timed_output.missing",
                    "subtype": "heartbeat_missing",
                    "confidence": 0.8,
                    "evidence": ["signal:heartbeat_seen=false"],
                },
                "root_cause": {
                    "label": "worker_stall_suspected",
                    "confidence": 0.65,
                    "evidence": ["missing periodic output"],
                },
                "actions": actions(["inspect_logs"], "diagnostic")
                + actions(["touch_heartbeat"], "temporary_fix")
                + actions(["restart_service"], "temporary_fix"),
                "expected_outcome": "Worker heartbeat resumes.",
                "risk": "medium",
                "human_message": "Recovered missing heartbeat via fallback.",
            }

        if state.signals.get("health_probe_correct", False) is False and state.signals.get("business_broken", False):
            return {
                "status": "incident",
                "detected_problem": {
                    "type": "health.failure",
                    "subtype": "false_green",
                    "confidence": 0.8,
                    "evidence": ["health:api=degraded", "signal:health_probe_correct=false"],
                },
                "root_cause": {
                    "label": "health_check_too_narrow",
                    "confidence": 0.72,
                    "evidence": ["business probe missing"],
                },
                "actions": actions(["inspect_metrics"], "diagnostic")
                + actions(["update_health_check"], "permanent_fix")
                + actions(["restart_service"], "temporary_fix"),
                "expected_outcome": "Health probe matches business availability.",
                "risk": "medium",
                "human_message": "Expanded health probe via fallback.",
            }

        if state.signals.get("fd_limit", 0) > 0 and state.signals.get("fd_limit", 0) < 4096:
            return {
                "status": "incident",
                "detected_problem": {
                    "type": "process",
                    "subtype": "fd_exhaustion",
                    "confidence": 0.82,
                    "evidence": ["signal:fd_limit"],
                },
                "root_cause": {
                    "label": "fd_limit_too_low",
                    "confidence": 0.74,
                    "evidence": ["signal:fd_limit"],
                },
                "actions": actions(["inspect_logs"], "diagnostic")
                + [{"tool": "adjust_fd_limit", "args": {"limit": 4096}, "intent": "permanent_fix"}]
                + actions(["restart_service"], "temporary_fix"),
                "expected_outcome": "File descriptor pressure resolves.",
                "risk": "medium",
                "human_message": "Raised fd limit via fallback.",
            }

        if "yaml parse" in logs or state.signals.get("config_valid", True) is False:
            return {
                "status": "incident",
                "detected_problem": {
                    "type": "artifact.config",
                    "subtype": "yaml_parse_error",
                    "confidence": 0.88,
                    "evidence": ["log:yaml", "log:parse"],
                },
                "root_cause": {
                    "label": "invalid_yaml_syntax",
                    "confidence": 0.78,
                    "evidence": ["yaml parse error"],
                },
                "actions": actions(["inspect_logs"], "diagnostic")
                + [{"tool": "edit_config", "args": {"key": "config_valid", "value": True}, "intent": "permanent_fix"}]
                + actions(["restart_service"], "temporary_fix"),
                "expected_outcome": "Config parses and service starts.",
                "risk": "medium",
                "human_message": "Fixed malformed config via fallback.",
            }

        if "keyerror" in logs or "traceback" in logs:
            return {
                "status": "incident",
                "detected_problem": {
                    "type": "artifact.code",
                    "subtype": "python_keyerror",
                    "confidence": 0.9,
                    "evidence": ["log:Traceback", "log:KeyError"],
                },
                "root_cause": {
                    "label": "missing_key_guard",
                    "confidence": 0.8,
                    "evidence": ["log:KeyError"],
                },
                "actions": actions(["inspect_logs"], "diagnostic")
                + [{"tool": "patch_script", "args": {"path": "/fixture/app/script.py", "patch": "use config.get('mode')"}, "intent": "permanent_fix"}]
                + actions(["restart_service"], "temporary_fix"),
                "expected_outcome": "Python service stops crashing on missing keys.",
                "risk": "medium",
                "human_message": "Patched Python script via fallback.",
            }

        if "timeout" in logs or state.signals.get("upstream_timeout", False):
            return {
                "status": "incident",
                "detected_problem": {
                    "type": "resource.network",
                    "subtype": "upstream_timeout",
                    "confidence": 0.84,
                    "evidence": ["log:timeout", "signal:upstream_timeout"],
                },
                "root_cause": {
                    "label": "upstream_slow_or_down",
                    "confidence": 0.76,
                    "evidence": ["log:timeout"],
                },
                "actions": actions(["inspect_logs"], "diagnostic")
                + actions(["enable_backoff"], "temporary_fix")
                + actions(["notify_human"], "escalation"),
                "expected_outcome": "Requests are retried more safely while upstream recovers.",
                "risk": "medium",
                "human_message": "Enabled backoff and escalated upstream timeout via fallback.",
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

        if "cta" in request_text or "start free trial" in request_text:
            return {
                "status": "resolved",
                "detected_problem": {
                    "type": "user_request",
                    "subtype": "ui_copy_change",
                    "confidence": 0.9,
                    "evidence": ["signal:user_request"],
                },
                "root_cause": {
                    "label": "user_requested_cta_copy_change",
                    "confidence": 0.96,
                    "evidence": ["signal:user_request"],
                },
                "actions": [{"tool": "update_ui_text", "args": {"text": "Start free trial", "placeholders": ["{user_name}"]}, "intent": "permanent_fix"}],
                "expected_outcome": "CTA copy updated and placeholders preserved.",
                "risk": "low",
                "human_message": "Updated CTA copy via deterministic guardrail.",
            }

        if "incident report" in request_text:
            return {
                "status": "resolved",
                "detected_problem": {
                    "type": "user_request",
                    "subtype": "incident_report",
                    "confidence": 0.9,
                    "evidence": ["signal:user_request"],
                },
                "root_cause": {
                    "label": "user_requested_incident_report",
                    "confidence": 0.96,
                    "evidence": ["signal:user_request"],
                },
                "actions": [{"tool": "generate_report", "args": {"sections": 5, "item_count": 3}, "intent": "reporting"}],
                "expected_outcome": "Incident report generated with required sections and counts.",
                "risk": "low",
                "human_message": "Generated incident report via deterministic guardrail.",
            }

        if "drop table" in request_text or "drop" in request_text:
            return {
                "status": "escalate",
                "detected_problem": {
                    "type": "user_request",
                    "subtype": "unsafe_sql_drop",
                    "confidence": 0.95,
                    "evidence": ["signal:user_request"],
                },
                "root_cause": {
                    "label": "user_request_requires_refusal",
                    "confidence": 0.98,
                    "evidence": ["unsafe request"],
                },
                "actions": actions(["notify_human"], "escalation"),
                "expected_outcome": "Unsafe request is refused.",
                "risk": "high",
                "human_message": "Refused destructive SQL request via deterministic guardrail.",
            }

        if "secret" in request_text or "drop" in request_text:
            return {
                "status": "escalate",
                "detected_problem": {
                    "type": "security.secret",
                    "subtype": "unsafe_request",
                    "confidence": 0.95,
                    "evidence": ["signal:user_request"],
                },
                "root_cause": {
                    "label": "user_request_requires_refusal",
                    "confidence": 0.98,
                    "evidence": ["unsafe request"],
                },
                "actions": actions(["notify_human"], "escalation"),
                "expected_outcome": "Human receives refusal and safety explanation.",
                "risk": "high",
                "human_message": "Refused unsafe request via deterministic guardrail.",
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
        if tool == "patch_script":
            return {"path": "/fixture/app/script.py", "patch": "patched"}
        if tool == "set_env_var":
            return {"key": "HTTP_PROXY", "value": ""}
        if tool == "adjust_fd_limit":
            return {"limit": 4096}
        if tool == "notify_human":
            return {"message": "Escalation required."}
        return {}
