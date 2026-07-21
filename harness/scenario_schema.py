from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import re
from typing import Any


@dataclass
class ExpectedSpec:
    problem_type: str
    subtype: str
    root_cause_label: str
    required_evidence: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    disallowed_actions: list[str] = field(default_factory=list)
    fix_validation: list[str] = field(default_factory=list)
    durability_validation: list[str] = field(default_factory=list)
    escalation_expected: bool = False


@dataclass
class SafetySpec:
    sandbox: str = "simulated"
    allowed_paths: list[str] = field(default_factory=list)


@dataclass
class DifficultySpec:
    detect: str = "medium"
    temporary_fix: str = "medium"
    permanent_fix: str = "medium"
    regression_risk: str = "medium"
    edge_realism: str = "medium"


@dataclass
class RoundInput:
    round: int
    metrics: dict[str, float] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    health: dict[str, str] = field(default_factory=dict)
    signals: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scenario:
    id: str
    title: str
    category: str
    description: str
    fault_round: int
    deadline_round: int
    max_score_class: str
    difficulty: DifficultySpec
    expected: ExpectedSpec
    safety: SafetySpec
    baseline_state: dict[str, Any]
    rounds: list[RoundInput]


def _required_str(v: Any, name: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"missing/invalid string: {name}")
    return v.strip()


def _required_int(v: Any, name: str) -> int:
    if not isinstance(v, int):
        raise ValueError(f"missing/invalid int: {name}")
    return v


def scenario_from_dict(data: dict[str, Any]) -> Scenario:
    expected_raw = data.get("expected") or {}
    safety_raw = data.get("safety") or {}
    difficulty_raw = data.get("difficulty") or {}
    rounds_raw = data.get("rounds") or []

    expected = ExpectedSpec(
        problem_type=_required_str(expected_raw.get("problem_type"), "expected.problem_type"),
        subtype=_required_str(expected_raw.get("subtype"), "expected.subtype"),
        root_cause_label=_required_str(expected_raw.get("root_cause_label"), "expected.root_cause_label"),
        required_evidence=[str(x) for x in expected_raw.get("required_evidence", [])],
        allowed_actions=[str(x) for x in expected_raw.get("allowed_actions", [])],
        disallowed_actions=[str(x) for x in expected_raw.get("disallowed_actions", [])],
        fix_validation=[str(x) for x in expected_raw.get("fix_validation", [])],
        durability_validation=[str(x) for x in expected_raw.get("durability_validation", [])],
        escalation_expected=bool(expected_raw.get("escalation_expected", False)),
    )
    safety = SafetySpec(
        sandbox=str(safety_raw.get("sandbox", "simulated")),
        allowed_paths=[str(x) for x in safety_raw.get("allowed_paths", [])],
    )
    difficulty = DifficultySpec(
        detect=str(difficulty_raw.get("detect", "medium")),
        temporary_fix=str(difficulty_raw.get("temporary_fix", "medium")),
        permanent_fix=str(difficulty_raw.get("permanent_fix", "medium")),
        regression_risk=str(difficulty_raw.get("regression_risk", "medium")),
        edge_realism=str(difficulty_raw.get("edge_realism", "medium")),
    )
    rounds: list[RoundInput] = []
    for r in rounds_raw:
        rounds.append(
            RoundInput(
                round=_required_int(r.get("round"), "round.round"),
                metrics=r.get("metrics") if isinstance(r.get("metrics"), dict) else {},
                logs=[str(x) for x in r.get("logs", [])],
                health=r.get("health") if isinstance(r.get("health"), dict) else {},
                signals=r.get("signals") if isinstance(r.get("signals"), dict) else {},
            )
        )
    return Scenario(
        id=_required_str(data.get("id"), "id"),
        title=_required_str(data.get("title"), "title"),
        category=_required_str(data.get("category"), "category"),
        description=_required_str(data.get("description"), "description"),
        fault_round=_required_int(data.get("fault_round"), "fault_round"),
        deadline_round=_required_int(data.get("deadline_round"), "deadline_round"),
        max_score_class=str(data.get("max_score_class", "fix_permanent")),
        difficulty=difficulty,
        expected=expected,
        safety=safety,
        baseline_state=data.get("baseline_state") if isinstance(data.get("baseline_state"), dict) else {},
        rounds=rounds,
    )


def load_scenarios(scenarios_dir: Path) -> list[Scenario]:
    canonical_categories = {
        "cpu",
        "memory",
        "disk",
        "network",
        "process",
        "logs",
        "health",
        "timed_output",
        "config",
        "data",
        "artifact",
        "user_request",
        "security",
        "agent",
        "mixed",
    }
    canonical_id = re.compile(r"^[A-Z]+-\d{3}\.json$")
    files = [
        path
        for path in sorted(scenarios_dir.rglob("*.json"))
        if path.parent.name in canonical_categories and canonical_id.match(path.name)
    ]
    scenarios: list[Scenario] = []
    for path in files:
        raw = json.loads(path.read_text(encoding="utf-8"))
        scenarios.append(scenario_from_dict(raw))
    return scenarios
