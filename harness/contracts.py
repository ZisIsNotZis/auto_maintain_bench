from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HarnessContract:
    root: Path
    system_prompt: str
    bash_tool: dict[str, Any]


def load_harness_contract(root: Path) -> HarnessContract:
    return HarnessContract(
        root=root,
        system_prompt=(root / "PROMPT.md").read_text(encoding="utf-8").strip(),
        bash_tool=_load_json(root / "bash_tool.schema.json"),
    )
def load_grammar(root: Path, name: str) -> str:
    return (root / "schemas" / f"{name}.gbnf").read_text(encoding="utf-8").strip()


def validate_telemetry(
    telemetry: dict[str, Any],
) -> None:
    if not isinstance(telemetry, dict):
        raise ValueError("telemetry must be a JSON object")
    observed_at = telemetry.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at:
        raise ValueError("telemetry.observed_at must be a non-empty string")
    _parse_timestamp(observed_at, "telemetry.observed_at")
    if not isinstance(telemetry.get("services"), list):
        raise ValueError("telemetry.services must be an array")
    if not isinstance(telemetry.get("escalating"), list):
        raise ValueError("telemetry.escalating must be an array")
    if not isinstance(telemetry.get("collection_errors"), list):
        raise ValueError("telemetry.collection_errors must be an array")
    observed_at = str(telemetry["observed_at"])
    _validate_trend(
        telemetry["cpu"],
        current_key="usage_pct",
        trend_key="usage_pct_trend",
        observed_at=observed_at,
        path="cpu",
    )
    _validate_trend(
        telemetry["memory"],
        current_key="used_pct",
        trend_key="used_pct_trend",
        observed_at=observed_at,
        path="memory",
    )
    for index, filesystem in enumerate(telemetry["filesystems"]):
        _validate_trend(
            filesystem,
            current_key="used_pct",
            trend_key="used_pct_trend",
            observed_at=observed_at,
            path=f"filesystems[{index}]",
        )
    for index, interface in enumerate(telemetry["network_interfaces"]):
        for current_key in ("rx_bytes_s", "tx_bytes_s"):
            _validate_trend(
                interface,
                current_key=current_key,
                trend_key=f"{current_key}_trend",
                observed_at=observed_at,
                path=f"network_interfaces[{index}]",
            )
    for index, service in enumerate(telemetry["services"]):
        for current_key in ("cpu_pct", "memory_bytes"):
            _validate_trend(
                service,
                current_key=current_key,
                trend_key=f"{current_key}_trend",
                observed_at=observed_at,
                path=f"services[{index}]",
            )
        if "memory_pct" in service:
            val = service["memory_pct"]
            if not isinstance(val, (int, float)):
                raise ValueError(f"services[{index}].memory_pct must be numeric")
        if "last_output_at" in service:
            _parse_timestamp(str(service["last_output_at"]), f"services[{index}].last_output_at")
        for field_name in ("stdout", "stderr"):
            log_obj = service.get(field_name)
            if isinstance(log_obj, dict):
                if "new_line_count" in log_obj and not isinstance(log_obj["new_line_count"], int):
                    raise ValueError(f"services[{index}].{field_name}.new_line_count must be an int")
                if "lines" in log_obj and not isinstance(log_obj["lines"], list):
                    raise ValueError(f"services[{index}].{field_name}.lines must be an array")
        req = service.get("requests")
        if isinstance(req, dict):
            for key in ("rate_s", "error_pct", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms"):
                if key in req and not isinstance(req[key], (int, float)):
                    raise ValueError(f"services[{index}].requests.{key} must be numeric")
            if "error_pct_trend" in req:
                _validate_trend(req, current_key="error_pct", trend_key="error_pct_trend", observed_at=observed_at, path=f"services[{index}].requests")
        queue = service.get("queue")
        if isinstance(queue, dict):
            _validate_trend(
                queue,
                current_key="depth",
                trend_key="depth_trend",
                observed_at=observed_at,
                path=f"services[{index}].queue",
            )
    # Validate notable_processes if present
    for index, proc in enumerate(telemetry.get("notable_processes", [])):
        if not isinstance(proc, dict):
            raise ValueError(f"notable_processes[{index}] must be an object")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_trend(
    owner: dict[str, Any],
    *,
    current_key: str,
    trend_key: str,
    observed_at: str,
    path: str,
) -> None:
    trend = owner.get(trend_key)
    if trend is None:
        return
    if not isinstance(trend, dict):
        raise ValueError(f"{path}.{trend_key} must be a timestamp/value object")
    if observed_at not in trend:
        raise ValueError(f"{path}.{trend_key} must include observed_at {observed_at}")
    for key, value in trend.items():
        _parse_timestamp(str(key), f"{path}.{trend_key}")
        if not isinstance(value, (int, float)):
            raise ValueError(f"{path}.{trend_key} values must be numeric")
    if trend[observed_at] != owner.get(current_key):
        raise ValueError(
            f"{path}.{trend_key}[observed_at] must equal {path}.{current_key}"
        )


def _parse_timestamp(value: str, path: str) -> None:
    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{path} must be ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{path} must include timezone")
