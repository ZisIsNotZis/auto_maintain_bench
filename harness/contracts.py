from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkContract:
    id: str
    root: Path
    manifest: dict[str, Any]
    system_prompt: str
    bash_tool: dict[str, Any]


def load_benchmark_contract(root: Path) -> BenchmarkContract:
    manifest = _load_json(root / "manifest.json")
    return BenchmarkContract(
        id=str(manifest["id"]),
        root=root,
        manifest=manifest,
        system_prompt=(root / str(manifest["system_prompt"])).read_text(encoding="utf-8").strip(),
        bash_tool=_load_json(root / str(manifest["bash_tool"])),
    )


def load_prompt_catalog(root: Path) -> dict[str, Any]:
    return _load_json(root / "prompts" / "legacy_protocol.json")


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
        queue = service.get("queue")
        if isinstance(queue, dict):
            _validate_trend(
                queue,
                current_key="depth",
                trend_key="depth_trend",
                observed_at=observed_at,
                path=f"services[{index}].queue",
            )


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
