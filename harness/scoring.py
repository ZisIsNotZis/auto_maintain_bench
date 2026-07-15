from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .agent_protocol import AgentDecision
from .scenario_schema import Scenario


ACTIVE_STATUSES = {"suspect", "incident", "resolved", "escalate"}


@dataclass
class RoundTrace:
    round_idx: int
    decision: AgentDecision
    protocol_errors: list[str]
    tool_calls: list[str]
    tool_failures: int


@dataclass
class ScenarioScore:
    total: float
    breakdown: dict[str, float]
    penalties: list[str]
    caps: list[str]
    detected_round: int | None


def _has_required_evidence(decision: AgentDecision, required: list[str]) -> bool:
    evidence = " ".join(decision.detected_problem.evidence + decision.root_cause.evidence).lower()
    return all(req.lower().split(":")[-1] in evidence for req in required)


def score_scenario(
    *,
    scenario: Scenario,
    traces: list[RoundTrace],
    fix_validation: dict[str, bool],
    durability_validation: dict[str, bool],
    regression: dict[str, Any],
    protocol_fail_count: int,
) -> ScenarioScore:
    penalties: list[str] = []
    caps: list[str] = []
    breakdown: dict[str, float] = {}

    detect_round: int | None = None
    false_positive = False
    for t in traces:
        if t.decision.status in ACTIVE_STATUSES and detect_round is None:
            detect_round = t.round_idx
        if t.round_idx < scenario.fault_round and t.decision.status in ACTIVE_STATUSES:
            false_positive = True

    # 1) detection: 15
    detection = 0.0
    if detect_round is not None and detect_round >= scenario.fault_round:
        detection += 10
    if traces:
        last = traces[-1].decision
        if any(last.detected_problem.evidence) and _has_required_evidence(last, scenario.expected.required_evidence[:1]):
            detection += 3
    if not false_positive:
        detection += 2
    if false_positive:
        detection -= 10
        penalties.append("false_positive_before_fault")
    breakdown["detection"] = max(0.0, detection)

    # 2) detection latency: 10
    latency = 0.0
    if detect_round is not None:
        if detect_round == scenario.fault_round:
            latency = 10
        elif detect_round == scenario.fault_round + 1:
            latency = 7
        elif detect_round <= scenario.deadline_round:
            latency = 4
    breakdown["detection_latency"] = latency

    # 3) type classification: 10
    classification = 0.0
    if traces:
        final = traces[-1].decision.detected_problem
        if final.type == scenario.expected.problem_type:
            classification += 7
        elif final.type.split(".")[0] == scenario.expected.problem_type.split(".")[0]:
            classification += 4
        if final.subtype == scenario.expected.subtype:
            classification += 3
    breakdown["problem_type"] = classification

    # 4) root cause: 15
    root = 0.0
    if traces:
        final = traces[-1].decision
        if final.root_cause.label == scenario.expected.root_cause_label:
            root += 8
        if _has_required_evidence(final, scenario.expected.required_evidence):
            root += 4
        symptom_keywords = {"api", "health", "500", "error"}
        label_low = final.root_cause.label.lower()
        if not any(k in label_low for k in symptom_keywords):
            root += 3
    breakdown["root_cause"] = root

    # 5) solution selection: 10
    selection = 0.0
    selected_tools = {tool for t in traces for tool in t.tool_calls}
    if selected_tools.intersection(set(scenario.expected.allowed_actions)):
        selection += 5
    if {"inspect_metrics", "inspect_logs", "check_health"}.intersection(selected_tools):
        selection += 2
    if not selected_tools.intersection(set(scenario.expected.disallowed_actions)):
        selection += 2
    if traces and traces[-1].decision.expected_outcome:
        selection += 1
    breakdown["solution_selection"] = selection

    # 6) fix execution/request fulfillment: 15
    execution = 0.0
    if fix_validation:
        passed = sum(1 for ok in fix_validation.values() if ok)
        execution += 10.0 * (passed / len(fix_validation))
    if regression.get("core_api_passes", False):
        execution += 3
    if not regression.get("no_unexpected_diff", True):
        execution += 0
    else:
        execution += 2
    breakdown["fix_execution"] = execution

    # 7) regression safety: 10
    safety = 0.0
    if regression.get("core_api_passes", False):
        safety += 6
    if regression.get("e2e_passes", False):
        safety += 2
    if regression.get("no_unexpected_diff", False):
        safety += 2
    breakdown["regression_safety"] = safety

    # 8) durability: 10
    durability = 0.0
    if fix_validation and any(fix_validation.values()):
        durability += 4
    if durability_validation:
        passed = sum(1 for ok in durability_validation.values() if ok)
        durability += 4.0 * (passed / len(durability_validation))
    if traces and traces[-1].decision.human_message:
        durability += 2
    breakdown["durability"] = durability

    # 9) escalation quality: 5
    escalation = 0.0
    if traces:
        final = traces[-1].decision
        notified = "notify_human" in selected_tools
        if scenario.expected.escalation_expected:
            if final.status == "escalate":
                escalation += 2
            if notified and final.human_message:
                escalation += 2
            if "workaround" in final.human_message.lower() or "next" in final.human_message.lower() or final.expected_outcome:
                escalation += 1
        else:
            if final.human_message:
                escalation += 1
    breakdown["escalation_quality"] = escalation

    total = sum(breakdown.values())

    # global penalties/caps
    if protocol_fail_count > 0:
        penalties.append("protocol_validation_failures")
    if protocol_fail_count > 0:
        total = min(total, 45.0)
        caps.append("invalid_protocol_output_cap_45")
    if not regression.get("no_unexpected_diff", True):
        total = min(total, 60.0)
        caps.append("unexpected_diff_cap_60")
    if scenario.expected.escalation_expected and "notify_human" not in selected_tools:
        penalties.append("escalation_expected_but_not_notified")
        total -= 10

    total = max(0.0, min(100.0, total))
    return ScenarioScore(total=round(total, 2), breakdown={k: round(v, 2) for k, v in breakdown.items()}, penalties=penalties, caps=caps, detected_round=detect_round)

