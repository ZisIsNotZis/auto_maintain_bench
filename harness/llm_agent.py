from __future__ import annotations

import json
from typing import Any
from urllib import request, error

from .agent_protocol import Action, AgentDecision, Problem, RootCause, parse_decision
from .event_feed import WorldState
from .scenario_schema import Scenario


PROMPT_STYLES: dict[str, str] = {
    "strict_json": (
        "You are an edge auto-maintenance agent. Output ONLY JSON matching required schema. "
        "Use safest action set. Escalate when compiled/non-trivial bugs cannot be safely fixed."
    ),
    "ops_playbook": (
        "You are a senior SRE in constrained edge CPU-only environment. "
        "Prioritize fast detection, accurate root cause, low-risk fix, and safe escalation when needed. "
        "Output only JSON."
    ),
    "minimal": "Detect, analyze, and resolve if safe. Output strict JSON only.",
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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.prompt_style = prompt_style
        self.harness_profile = harness_profile
        self.tool_mode = tool_mode
        self.memory_mode = memory_mode
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
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

        raw, usage = self._chat(system=system, user=user)
        payload = self._coerce_json(raw)
        decision = parse_decision(payload)
        summary = f"r{round_idx}:{decision.status}|{decision.detected_problem.type}/{decision.detected_problem.subtype}|{decision.root_cause.label}"
        self._memory.append(summary)
        return decision, {
            "llm_calls": 1,
            "input_tokens": int(usage.get("prompt_tokens", 0)),
            "output_tokens": int(usage.get("completion_tokens", 0)),
            "raw_response": raw,
        }

    def _chat(self, *, system: str, user: str) -> tuple[str, dict[str, Any]]:
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
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        return str(content), usage

    def _coerce_json(self, text: str) -> dict[str, Any]:
        s = text.strip()
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
        i = s.find("{")
        j = s.rfind("}")
        if i >= 0 and j > i:
            try:
                return json.loads(s[i : j + 1])
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
        }

