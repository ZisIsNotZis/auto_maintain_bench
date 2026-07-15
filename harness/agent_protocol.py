from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_STATUS = {"ok", "suspect", "incident", "resolved", "escalate", "need_more_info"}
VALID_RISK = {"low", "medium", "high"}
VALID_INTENTS = {"temporary_fix", "permanent_fix", "diagnostic", "rollback", "escalation", "reporting"}


@dataclass
class Action:
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    intent: str = "diagnostic"


@dataclass
class Problem:
    type: str = "unknown"
    subtype: str = "unknown"
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class RootCause:
    label: str = "unknown"
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class AgentDecision:
    status: str
    detected_problem: Problem
    root_cause: RootCause
    actions: list[Action]
    expected_outcome: str
    risk: str
    human_message: str


def decision_to_dict(decision: AgentDecision) -> dict[str, Any]:
    return {
        "status": decision.status,
        "detected_problem": {
            "type": decision.detected_problem.type,
            "subtype": decision.detected_problem.subtype,
            "confidence": decision.detected_problem.confidence,
            "evidence": list(decision.detected_problem.evidence),
        },
        "root_cause": {
            "label": decision.root_cause.label,
            "confidence": decision.root_cause.confidence,
            "evidence": list(decision.root_cause.evidence),
        },
        "actions": [{"tool": a.tool, "args": a.args, "intent": a.intent} for a in decision.actions],
        "expected_outcome": decision.expected_outcome,
        "risk": decision.risk,
        "human_message": decision.human_message,
    }


def parse_decision(payload: dict[str, Any]) -> AgentDecision:
    problem = payload.get("detected_problem") or {}
    root = payload.get("root_cause") or {}
    actions_payload = payload.get("actions") or []
    actions: list[Action] = []
    for raw in actions_payload:
        if not isinstance(raw, dict):
            continue
        actions.append(
            Action(
                tool=str(raw.get("tool", "")).strip(),
                args=raw.get("args") if isinstance(raw.get("args"), dict) else {},
                intent=str(raw.get("intent", "diagnostic")).strip(),
            )
        )
    return AgentDecision(
        status=str(payload.get("status", "")).strip(),
        detected_problem=Problem(
            type=str(problem.get("type", "unknown")).strip(),
            subtype=str(problem.get("subtype", "unknown")).strip(),
            confidence=float(problem.get("confidence", 0.0)),
            evidence=[str(e) for e in (problem.get("evidence") or [])],
        ),
        root_cause=RootCause(
            label=str(root.get("label", "unknown")).strip(),
            confidence=float(root.get("confidence", 0.0)),
            evidence=[str(e) for e in (root.get("evidence") or [])],
        ),
        actions=actions,
        expected_outcome=str(payload.get("expected_outcome", "")).strip(),
        risk=str(payload.get("risk", "")).strip(),
        human_message=str(payload.get("human_message", "")).strip(),
    )


def validate_decision_shape(decision: AgentDecision) -> list[str]:
    errors: list[str] = []
    if decision.status not in VALID_STATUS:
        errors.append(f"invalid_status:{decision.status}")
    if decision.risk not in VALID_RISK:
        errors.append(f"invalid_risk:{decision.risk}")
    if not decision.detected_problem.type:
        errors.append("missing_problem_type")
    if not decision.root_cause.label:
        errors.append("missing_root_cause_label")
    for i, action in enumerate(decision.actions):
        if not action.tool:
            errors.append(f"empty_tool_at:{i}")
        if action.intent not in VALID_INTENTS:
            errors.append(f"invalid_intent:{action.intent}@{i}")
    return errors

