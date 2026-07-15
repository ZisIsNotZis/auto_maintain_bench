from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .scenario_schema import Scenario, RoundInput


@dataclass
class WorldState:
    metrics: dict[str, float]
    logs: list[str]
    health: dict[str, str]
    signals: dict[str, Any]
    files: dict[str, str]
    db: dict[str, Any]
    changed_paths: set[str]
    service_restarted: bool = False
    human_notified: bool = False

    @classmethod
    def from_baseline(cls, baseline: dict[str, Any]) -> "WorldState":
        return cls(
            metrics=dict(baseline.get("metrics", {})),
            logs=list(baseline.get("logs", [])),
            health=dict(baseline.get("health", {})),
            signals=dict(baseline.get("signals", {})),
            files=dict(baseline.get("files", {})),
            db=dict(baseline.get("db", {})),
            changed_paths=set(),
        )


def apply_round_event(state: WorldState, event: RoundInput) -> None:
    if event.metrics:
        state.metrics.update({k: float(v) for k, v in event.metrics.items()})
    if event.logs:
        state.logs.extend(event.logs)
    if event.health:
        state.health.update({str(k): str(v) for k, v in event.health.items()})
    if event.signals:
        state.signals.update(event.signals)


def iter_rounds(scenario: Scenario) -> list[RoundInput]:
    return sorted(scenario.rounds, key=lambda r: r.round)

