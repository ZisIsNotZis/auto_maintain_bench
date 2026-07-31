from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, Protocol

from .maintenance_loop import WakeupResult


class WakeupLoop(Protocol):
    def run_wakeup(self, telemetry: dict[str, Any]) -> WakeupResult: ...


class MaintenanceDaemon:
    def __init__(
        self,
        *,
        loop: WakeupLoop,
        escalations: "EscalationStore",
        clock: Callable[[], str] | None = None,
        validator: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.loop = loop
        self.escalations = escalations
        self.clock = clock or _utc_now
        self.validator = validator

    def run_cycle(self, telemetry: dict[str, Any]) -> WakeupResult:
        wakeup = self.escalations.inject(telemetry)
        if self.validator is not None:
            self.validator(wakeup)
        result = self.loop.run_wakeup(wakeup)
        self.escalations.apply(result, now=self.clock())
        return result


class EscalationStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def inject(self, telemetry: dict[str, Any]) -> dict[str, Any]:
        enriched = deepcopy(telemetry)
        enriched["escalating"] = self._read()
        return enriched

    def apply(self, result: WakeupResult, *, now: str) -> None:
        active = self._read()
        if result.terminal == "escalate" and result.escalation_id:
            if not any(item["id"] == result.escalation_id for item in active):
                active = [
                    *active,
                    {
                        "id": result.escalation_id,
                        "level": result.escalation_level,
                        "message": result.message,
                        "raised_at": now,
                    },
                ]
            self._write(active)
            return
        if result.terminal == "escalate_none":
            remaining = [
                item for item in active
                if item["id"] != result.message
            ]
            self._write(remaining)

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        return [dict(item) for item in data if isinstance(item, dict)]

    def _write(self, active: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(active, handle, ensure_ascii=True, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except Exception:
            Path(temporary).unlink(missing_ok=True)
            raise


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
