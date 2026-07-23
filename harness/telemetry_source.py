from __future__ import annotations

from copy import deepcopy
import threading
import time
from typing import Any, Callable


class PeriodicTelemetrySource:
    def __init__(
        self,
        collector: Callable[[], dict[str, Any]],
        *,
        interval_s: float = 10.0,
    ) -> None:
        if interval_s <= 0:
            raise ValueError("telemetry interval must be positive")
        self.collector = collector
        self.interval_s = interval_s
        self._condition = threading.Condition()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._latest: dict[str, Any] | None = None
        self._published = 0
        self._consumed = 0
        self._error: Exception | None = None

    def __enter__(self) -> "PeriodicTelemetrySource":
        if self._thread is not None:
            raise RuntimeError("telemetry source is already running")
        self._thread = threading.Thread(
            target=self._collect_forever,
            name="maintenance-telemetry",
            daemon=True,
        )
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        with self._condition:
            self._condition.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self.interval_s * 2))
        self._thread = None

    def next(self) -> dict[str, Any]:
        with self._condition:
            self._condition.wait_for(self._ready)
            if self._error is not None:
                raise RuntimeError("telemetry collection failed") from self._error
            if self._latest is None:
                raise RuntimeError("telemetry source stopped before producing data")
            self._consumed = self._published
            return deepcopy(self._latest)

    def _ready(self) -> bool:
        return (
            self._error is not None
            or self._published > self._consumed
            or self._stop.is_set()
        )

    def _collect_forever(self) -> None:
        deadline = time.monotonic()
        while not self._stop.is_set():
            try:
                snapshot = self.collector()
                if not isinstance(snapshot, dict):
                    raise TypeError("telemetry collector must return a JSON object")
            except Exception as exc:
                with self._condition:
                    self._error = exc
                    self._condition.notify_all()
                return
            with self._condition:
                self._latest = deepcopy(snapshot)
                self._published += 1
                self._condition.notify_all()
            deadline += self.interval_s
            delay = max(0.0, deadline - time.monotonic())
            if self._stop.wait(delay):
                return
