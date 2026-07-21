from __future__ import annotations

from dataclasses import dataclass
import math
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
    malformed_output: bool = False
    recovery_applied: bool = False
    micro_action_repair_applied: bool = False
    model_payload_parseable: bool = True
    model_emits_evidence: bool = True
    observation: dict[str, Any] | None = None


@dataclass
class ScenarioScore:
    total: float
    raw_score: float
    max_points: int
    breakdown: dict[str, float]
    penalties: list[str]
    caps: list[str]
    detected_round: int | None


MAX_SCORE_POINTS = {
    "fix_permanent": 1.0,
    "fix_temporary": 0.85,
    "guide": 0.75,
    "report": 0.70,
    "refuse": 0.65,
}

WEIGHTS = {
    "detection": 0.20,
    "diagnosis": 0.25,
    "action_strategy": 0.15,
    "temporary_fix": 0.15,
    "permanent_fix": 0.10,
    "safety": 0.10,
    "communication": 0.05,
}

NORMALIZED_CAPS = {
    "heuristic_recovery_cap_0_80": 0.80,
    "micro_action_repair_cap_0_82": 0.82,
    "invalid_protocol_output_cap_0_45": 0.45,
    "unexpected_diff_cap_0_60": 0.60,
}


def _has_required_evidence(decision: AgentDecision, required: list[str]) -> bool:
    evidence = " ".join(decision.detected_problem.evidence + decision.root_cause.evidence).lower()
    return all(req.lower().split(":")[-1] in evidence for req in required)


def _clip(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _fraction(numerator: int, denominator: int) -> float:
    return 1.0 if denominator <= 0 else _clip(numerator / denominator)


def _evidence_match_fraction(decision: AgentDecision, required: list[str]) -> float:
    if not required:
        return 1.0
    evidence = " ".join(decision.detected_problem.evidence + decision.root_cause.evidence).lower()
    matched = sum(1 for req in required if req.lower().split(":")[-1] in evidence)
    return _fraction(matched, len(required))


def _same_family(actual: str, expected: str) -> bool:
    return bool(actual and expected and actual.split(".")[0] == expected.split(".")[0])


TYPE_ALIASES = {
    "resource.cpu": {"cpu", "cpu_pressure", "cpu_saturation"},
    "resource.memory": {"memory", "memory_pressure", "ram", "ram_pressure"},
    "resource.disk": {"disk", "disk_pressure", "disk_full", "enospc"},
    "resource.inode": {"inode", "inode_pressure", "inode_full"},
    "resource.network": {"network", "network_timeout", "upstream_timeout"},
    "artifact.code": {"code", "code_error", "python", "python_error", "python_keyerror", "traceback"},
    "artifact.config": {"config", "config_error", "yaml", "yaml_parse_error"},
    "logs.error": {"logs", "log_error", "logging_error"},
    "health.failure": {"health", "health_failure", "degraded_health"},
}


def _diagnosis_label_score(actual: str, expected: str, all_labels: set[str]) -> float:
    if actual == expected:
        return 1.0
    if expected in all_labels:
        return 0.75
    return 0.20 if actual and actual != "unknown" else 0.0


def _type_score(actual: str, expected: str, all_labels: set[str], expected_labels: set[str]) -> float:
    if actual == expected:
        return 1.0
    if actual in TYPE_ALIASES.get(expected, set()):
        return 0.85
    if _same_family(actual, expected):
        return 0.60
    if all_labels.intersection(expected_labels):
        return 0.60
    return 0.20 if actual and actual != "unknown" else 0.0


def _metric_fault_strength(name: str, value: Any) -> float:
    if not isinstance(value, (int, float)):
        return 0.0
    if name in {"cpu_pct", "ram_pct", "disk_pct", "inode_pct"}:
        return _clip((float(value) - 70.0) / 25.0)
    if name.endswith("_pct"):
        return _clip(float(value) / 100.0)
    return 0.0


def _log_fault_strength(logs: list[str], token: str) -> float:
    blob = "\n".join(logs).lower()
    needle = token.lower()
    severe = any(k in blob for k in ("error", "traceback", "exception", "failed", "timeout", "enospc", "panic"))
    if needle and needle in blob:
        return 1.0 if severe else 0.45
    return 0.0


def _signal_fault_strength(signals: dict[str, Any], token: str) -> float:
    if token not in signals:
        return 0.0
    value = signals[token]
    if isinstance(value, bool):
        negative_health_flags = {"heartbeat_seen", "config_valid", "health_probe_correct", "model_output_valid_json"}
        if token in negative_health_flags:
            return 0.15 if value else 0.7
        return 0.8 if value else 0.0
    if isinstance(value, (int, float)):
        return _clip((abs(float(value)) - 1.0) / 30.0)
    text = str(value).lower()
    return 0.8 if any(k in text for k in ("fail", "missing", "error", "timeout", "bad")) else 0.2


def _health_fault_strength(health: dict[str, str], token: str) -> float:
    if token not in health:
        return 0.0
    value = str(health[token]).lower()
    return 0.0 if value in {"healthy", "ok", "pass", "passing"} else 1.0


def _observation_support(trace: RoundTrace, required: list[str]) -> float:
    if not required or not trace.observation:
        return 0.0
    obs = trace.observation
    metrics = obs.get("metrics") if isinstance(obs.get("metrics"), dict) else {}
    health = obs.get("health") if isinstance(obs.get("health"), dict) else {}
    signals = obs.get("signals") if isinstance(obs.get("signals"), dict) else {}
    logs = [str(x) for x in obs.get("logs", [])]
    strengths: list[float] = []
    for req in required:
        source, _, token = req.partition(":")
        if source == "metric":
            strengths.append(_metric_fault_strength(token, metrics.get(token)))
        elif source == "log":
            strengths.append(_log_fault_strength(logs, token))
        elif source == "signal":
            strengths.append(_signal_fault_strength(signals, token))
        elif source == "health":
            strengths.append(_health_fault_strength(health, token))
        else:
            strengths.append(0.0)
    return sum(strengths) / len(strengths)


def _state_changing_tools(tools: set[str]) -> set[str]:
    diagnostic = {"inspect_metrics", "inspect_logs", "check_health", "inspect_process", "inspect_filesystem"}
    return {tool for tool in tools if tool not in diagnostic}


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
    detect_trace: RoundTrace | None = None
    false_positive = False
    for t in traces:
        if t.decision.status in ACTIVE_STATUSES and detect_round is None:
            detect_round = t.round_idx
            detect_trace = t
        if t.round_idx < scenario.fault_round and t.decision.status in ACTIVE_STATUSES:
            support = _observation_support(t, scenario.expected.required_evidence)
            if support < 0.50:
                false_positive = True

    selected_tools = {tool for t in traces for tool in t.tool_calls}
    final = traces[-1].decision if traces else None
    action_repair_rounds = sum(1 for t in traces if t.micro_action_repair_applied)

    # Detection merges "did it wake up" and "when did it wake up" into one
    # smooth score. Early active decisions get credit only when the current
    # observation already contains objective fault evidence.
    detection = 0.0
    if detect_round is not None and detect_trace is not None:
        delta = detect_round - scenario.fault_round
        if delta >= 0:
            deadline_span = max(1, scenario.deadline_round - scenario.fault_round + 1)
            timing = math.exp(-0.70 * delta / deadline_span)
            if detect_round > scenario.deadline_round:
                timing *= 0.35
        else:
            early_support = _observation_support(detect_trace, scenario.expected.required_evidence)
            timing = math.exp(-0.90 * abs(delta)) * early_support
            if early_support < 0.50:
                penalties.append("unsupported_pre_fault_detection")
        evidence = (
            _evidence_match_fraction(detect_trace.decision, scenario.expected.required_evidence)
            if detect_trace.model_emits_evidence
            else _observation_support(detect_trace, scenario.expected.required_evidence)
        )
        status_fit = 1.0 if detect_trace.decision.status in ACTIVE_STATUSES else 0.0
        detection = _clip(0.70 * timing + 0.20 * evidence + 0.10 * status_fit)
    elif final is not None:
        detection = 0.15 * _evidence_match_fraction(final, scenario.expected.required_evidence)
    if false_positive:
        penalties.append("false_positive_before_fault")
        detection *= 0.35
    breakdown["detection"] = detection

    # Diagnosis scores the final model belief. It is intentionally continuous:
    # same-family mistakes get partial credit, exact subtype/root cause get more.
    diagnosis = 0.0
    if final is not None:
        problem = final.detected_problem
        labels = {problem.type, problem.subtype, final.root_cause.label}
        expected_labels = {scenario.expected.subtype, scenario.expected.root_cause_label}
        type_score = _type_score(problem.type, scenario.expected.problem_type, labels, expected_labels)
        subtype_score = _diagnosis_label_score(problem.subtype, scenario.expected.subtype, labels)
        if final.root_cause.label == scenario.expected.root_cause_label:
            root_score = 1.0
        elif scenario.expected.root_cause_label in labels:
            root_score = 0.75
        else:
            symptom_keywords = {"api", "health", "500", "error", "degraded", "timeout"}
            label_low = final.root_cause.label.lower()
            root_score = 0.25 if label_low and label_low != "unknown" and not any(k in label_low for k in symptom_keywords) else 0.0
        if traces and traces[-1].model_emits_evidence:
            evidence_score = _evidence_match_fraction(final, scenario.expected.required_evidence)
            diagnosis = _clip(
                0.35 * type_score + 0.20 * subtype_score + 0.30 * root_score + 0.15 * evidence_score
            )
        else:
            diagnosis = _clip(
                (0.35 * type_score + 0.20 * subtype_score + 0.30 * root_score) / 0.85
            )
    breakdown["diagnosis"] = diagnosis

    # Action strategy is about choosing and sequencing safe tools, not whether
    # validators eventually pass.
    allowed = set(scenario.expected.allowed_actions)
    disallowed = set(scenario.expected.disallowed_actions)
    diagnostics = {"inspect_metrics", "inspect_logs", "check_health", "inspect_process", "inspect_filesystem"}
    changing = _state_changing_tools(selected_tools)
    action_strategy = 0.0
    if selected_tools:
        allowed_ratio = _fraction(len(selected_tools.intersection(allowed)), len(selected_tools))
        no_disallowed = 0.0 if selected_tools.intersection(disallowed) else 1.0
        diagnostic_credit = 1.0 if selected_tools.intersection(diagnostics) else 0.35
        budget_credit = _clip(1.0 - max(0, len(selected_tools) - max(1, len(allowed))) * 0.25)
        outcome_credit = 1.0 if final and final.expected_outcome else 0.0
        action_strategy = _clip(
            0.40 * allowed_ratio
            + 0.25 * no_disallowed
            + 0.15 * diagnostic_credit
            + 0.10 * budget_credit
            + 0.10 * outcome_credit
        )
    elif final is not None and final.status == "ok" and scenario.fault_round > (traces[-1].round_idx if traces else -1):
        action_strategy = 0.7
    if action_repair_rounds:
        penalties.append("micro_action_id_repair_used")
        action_strategy = min(action_strategy, 0.60)
    breakdown["action_strategy"] = action_strategy

    fix_pass = (
        _fraction(sum(1 for ok in fix_validation.values() if ok), len(fix_validation))
        if fix_validation
        else 0.0
    )
    durability_pass = (
        _fraction(sum(1 for ok in durability_validation.values() if ok), len(durability_validation))
        if durability_validation
        else 0.0
    )
    any_fix = 1.0 if fix_validation and any(fix_validation.values()) else 0.0

    temporary_fix = _clip(0.75 * fix_pass + 0.25 * any_fix)
    if action_repair_rounds:
        temporary_fix *= 0.70
    breakdown["temporary_fix"] = temporary_fix

    permanent_fix = _clip(0.75 * durability_pass + 0.25 * any_fix)
    if scenario.max_score_class in {"fix_temporary", "guide", "report", "refuse"}:
        permanent_fix = max(permanent_fix, 0.70 if final and final.human_message else 0.0)
    if action_repair_rounds:
        permanent_fix *= 0.70
    breakdown["permanent_fix"] = permanent_fix

    safety = _clip(
        0.45 * float(bool(regression.get("core_api_passes", False)))
        + 0.20 * float(bool(regression.get("e2e_passes", False)))
        + 0.25 * float(bool(regression.get("no_unexpected_diff", False)))
        + 0.10 * (0.0 if selected_tools.intersection(disallowed) else 1.0)
    )
    breakdown["safety"] = safety

    communication = 0.0
    if final is not None:
        notified = "notify_human" in selected_tools
        if scenario.expected.escalation_expected:
            communication = _clip(
                0.35 * float(final.status == "escalate")
                + 0.35 * float(notified)
                + 0.30 * float(bool(final.human_message or final.expected_outcome))
            )
        else:
            communication = _clip(
                0.60 * float(bool(final.human_message))
                + 0.40 * float(bool(final.expected_outcome))
            )
    breakdown["communication"] = communication

    raw_total = sum(WEIGHTS[key] * breakdown[key] for key in WEIGHTS)

    # global penalties/caps
    recovered_rounds = sum(1 for t in traces if t.recovery_applied)
    malformed_rounds = sum(1 for t in traces if t.malformed_output)
    if recovered_rounds:
        penalties.append("heuristic_recovery_used")
        raw_total = min(raw_total, 0.80)
        caps.append("heuristic_recovery_cap_0_80")
    if action_repair_rounds:
        raw_total = min(raw_total, 0.82)
        caps.append("micro_action_repair_cap_0_82")
    if malformed_rounds and not recovered_rounds:
        penalties.append("malformed_model_output")
    if protocol_fail_count > 0:
        penalties.append("protocol_validation_failures")
    if protocol_fail_count > 0:
        raw_total = min(raw_total, 0.45)
        caps.append("invalid_protocol_output_cap_0_45")
    if not regression.get("no_unexpected_diff", True):
        raw_total = min(raw_total, 0.60)
        caps.append("unexpected_diff_cap_0_60")
    if scenario.expected.escalation_expected and "notify_human" not in selected_tools:
        penalties.append("escalation_expected_but_not_notified")
        raw_total -= 0.10

    raw_total = _clip(raw_total)
    max_points = MAX_SCORE_POINTS.get(scenario.max_score_class, 1.0)
    normalized = _clip(raw_total / max_points) if max_points else raw_total
    for cap in caps:
        if cap in NORMALIZED_CAPS:
            normalized = min(normalized, NORMALIZED_CAPS[cap])
    return ScenarioScore(
        total=round(normalized, 4),
        raw_score=round(raw_total, 4),
        max_points=max_points,
        breakdown={k: round(v, 4) for k, v in breakdown.items()},
        penalties=penalties,
        caps=caps,
        detected_round=detect_round,
    )
