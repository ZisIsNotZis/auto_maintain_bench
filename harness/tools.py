from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .event_feed import WorldState
from .scenario_schema import Scenario


@dataclass
class ToolResult:
    ok: bool
    observation: dict[str, Any]
    changed_paths: list[str]


def execute_tool(
    *,
    tool: str,
    args: dict[str, Any],
    state: WorldState,
    scenario: Scenario,
) -> ToolResult:
    if tool == "inspect_metrics":
        return ToolResult(ok=True, observation={"metrics": dict(state.metrics)}, changed_paths=[])
    if tool == "inspect_logs":
        return ToolResult(ok=True, observation={"tail_logs": state.logs[-20:]}, changed_paths=[])
    if tool == "check_health":
        return ToolResult(ok=True, observation={"health": dict(state.health)}, changed_paths=[])
    if tool == "cleanup_tmp":
        state.metrics["disk_pct"] = max(10.0, state.metrics.get("disk_pct", 100.0) - 30.0)
        state.metrics["inode_pct"] = max(10.0, state.metrics.get("inode_pct", 100.0) - 25.0)
        state.changed_paths.add("/fixture/app/tmp")
        return ToolResult(
            ok=True,
            observation={"cleanup": "tmp cleaned", "disk_pct": state.metrics["disk_pct"], "inode_pct": state.metrics["inode_pct"]},
            changed_paths=["/fixture/app/tmp"],
        )
    if tool == "prune_logs":
        state.metrics["disk_pct"] = max(10.0, state.metrics.get("disk_pct", 100.0) - 35.0)
        state.signals["rotation_enabled"] = True
        state.changed_paths.add("/fixture/app/logrotate.conf")
        return ToolResult(ok=True, observation={"logs_pruned": True, "disk_pct": state.metrics["disk_pct"]}, changed_paths=["/fixture/app/logrotate.conf"])
    if tool == "trim_cache":
        state.metrics["ram_pct"] = max(15.0, state.metrics.get("ram_pct", 100.0) - 25.0)
        state.signals["cache_trimmed"] = True
        state.changed_paths.add("/fixture/app/config.yaml")
        return ToolResult(ok=True, observation={"cache_trimmed": True, "ram_pct": state.metrics["ram_pct"]}, changed_paths=["/fixture/app/config.yaml"])
    if tool == "edit_config":
        key = str(args.get("key", ""))
        value = args.get("value")
        if key:
            state.signals[key] = value
            if key in {"rotation_enabled", "retention_enabled"} and bool(value):
                state.metrics["disk_pct"] = max(10.0, state.metrics.get("disk_pct", 100.0) - 20.0)
            if key == "ui_copy_expected":
                state.signals["ui_copy_expected"] = value
            state.changed_paths.add("/fixture/app/config.yaml")
        return ToolResult(ok=True, observation={"config_set": {key: value}}, changed_paths=["/fixture/app/config.yaml"] if key else [])
    if tool == "patch_script":
        target = str(args.get("path", "/fixture/app/script.py"))
        state.files[target] = str(args.get("patch", "patched"))
        state.signals["source_patched"] = True
        state.changed_paths.add(target)
        return ToolResult(ok=True, observation={"patched": target}, changed_paths=[target])
    if tool == "set_env_var":
        key = str(args.get("key", ""))
        value = args.get("value")
        if key:
            state.signals[key] = value
            state.changed_paths.add("/fixture/app/.env")
        return ToolResult(ok=True, observation={"env_set": {key: value}}, changed_paths=["/fixture/app/.env"] if key else [])
    if tool == "touch_heartbeat":
        state.signals["heartbeat_seen"] = True
        state.health["worker"] = "healthy"
        return ToolResult(ok=True, observation={"heartbeat_seen": True}, changed_paths=[])
    if tool == "update_health_check":
        state.signals["health_probe_correct"] = True
        state.health["api"] = "healthy" if state.metrics.get("cpu_pct", 0) < 95 else state.health.get("api", "degraded")
        state.changed_paths.add("/fixture/app/health.py")
        return ToolResult(ok=True, observation={"health_probe_correct": True}, changed_paths=["/fixture/app/health.py"])
    if tool == "adjust_fd_limit":
        state.signals["fd_limit"] = int(args.get("limit", 4096))
        state.health["api"] = "healthy"
        state.changed_paths.add("/fixture/app/systemd/service.conf")
        return ToolResult(ok=True, observation={"fd_limit": state.signals["fd_limit"]}, changed_paths=["/fixture/app/systemd/service.conf"])
    if tool == "enable_backoff":
        state.signals["backoff_enabled"] = True
        state.changed_paths.add("/fixture/app/config.yaml")
        return ToolResult(ok=True, observation={"backoff_enabled": True}, changed_paths=["/fixture/app/config.yaml"])
    if tool == "fix_dns":
        state.signals["dns_ok"] = True
        state.health["network"] = "healthy"
        state.changed_paths.add("/fixture/app/resolv.conf")
        return ToolResult(ok=True, observation={"dns_ok": True}, changed_paths=["/fixture/app/resolv.conf"])
    if tool == "retry_output":
        state.signals["valid_json_recovered"] = True
        return ToolResult(ok=True, observation={"valid_json_recovered": True}, changed_paths=[])
    if tool == "enable_json_mode":
        state.signals["json_mode_enabled"] = True
        return ToolResult(ok=True, observation={"json_mode_enabled": True}, changed_paths=[])
    if tool == "tighten_grammar":
        state.signals["grammar_tightened"] = True
        return ToolResult(ok=True, observation={"grammar_tightened": True}, changed_paths=[])
    if tool == "restart_service":
        state.service_restarted = True
        disk_ok = state.metrics.get("disk_pct", 0) < 95.0 and state.metrics.get("inode_pct", 0) < 95.0
        cpu_ok = state.metrics.get("cpu_pct", 0) < 92.0
        ram_ok = state.metrics.get("ram_pct", 0) < 95.0
        db_ok = not state.signals.get("db_timeout_active", False)
        heartbeat_ok = state.signals.get("heartbeat_seen", True)
        rust_panic = bool(state.signals.get("rust_panic", False))
        if disk_ok and cpu_ok and ram_ok and db_ok and heartbeat_ok and not rust_panic:
            state.health["api"] = "healthy"
        return ToolResult(ok=True, observation={"service_restarted": True, "health": dict(state.health)}, changed_paths=[])
    if tool == "throttle_concurrency":
        state.metrics["cpu_pct"] = max(15.0, state.metrics.get("cpu_pct", 100.0) - 35.0)
        state.signals["worker_multiplier"] = 2
        state.changed_paths.add("/fixture/app/config.yaml")
        return ToolResult(
            ok=True,
            observation={"worker_multiplier": 2, "cpu_pct": state.metrics["cpu_pct"]},
            changed_paths=["/fixture/app/config.yaml"],
        )
    if tool == "replace_asset":
        target = str(args.get("path", "/fixture/app/static/logo.png"))
        state.files[target] = str(args.get("content", "new_logo_asset"))
        state.changed_paths.add(target)
        return ToolResult(ok=True, observation={"asset_replaced": target}, changed_paths=[target])
    if tool == "update_ui_text":
        text = str(args.get("text", "Start 7-day trial"))
        placeholders = [str(x) for x in args.get("placeholders", []) if str(x)]
        content = " ".join([text, *placeholders]).strip()
        state.files["/fixture/app/templates/main.html"] = content
        state.signals["ui_copy_expected"] = text
        state.signals["ui_placeholder_tokens"] = placeholders
        state.signals["ui_placeholders_preserved"] = all(ph in content for ph in placeholders)
        state.changed_paths.add("/fixture/app/templates/main.html")
        return ToolResult(
            ok=True,
            observation={"updated": "/fixture/app/templates/main.html"},
            changed_paths=["/fixture/app/templates/main.html"],
        )
    if tool == "run_sql":
        ids = args.get("account_ids", [])
        state.db["last_batch_ids"] = ids
        state.db["affected_rows"] = len(ids) if isinstance(ids, list) else 0
        return ToolResult(ok=True, observation={"affected_rows": state.db["affected_rows"]}, changed_paths=[])
    if tool == "notify_human":
        state.human_notified = True
        return ToolResult(ok=True, observation={"notified": True, "message": args.get("message", "")}, changed_paths=[])
    if tool == "generate_report":
        sections = int(args.get("sections", 0))
        expected = int(args.get("item_count", 0))
        state.db["last_report"] = {"summary": "report generated", "sections": sections, "item_count": expected}
        state.files["/fixture/app/reports/incident_report.md"] = f"sections={sections};items={expected}"
        state.signals["report_generated"] = True
        state.signals["report_sections_valid"] = sections >= 5
        state.signals["report_counts_valid"] = expected >= 3
        return ToolResult(ok=True, observation={"report_generated": True, "sections": sections, "item_count": expected}, changed_paths=["/fixture/app/reports/incident_report.md"])

    return ToolResult(ok=False, observation={"error": f"unknown_tool:{tool}"}, changed_paths=[])


def run_fix_validations(scenario: Scenario, state: WorldState) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for rule in scenario.expected.fix_validation:
        if rule == "disk_below_threshold":
            checks[rule] = state.metrics.get("disk_pct", 100.0) < 95.0 and state.metrics.get("inode_pct", 100.0) < 95.0
        elif rule == "cpu_below_threshold":
            checks[rule] = state.metrics.get("cpu_pct", 100.0) < 90.0
        elif rule == "api_healthy":
            checks[rule] = state.health.get("api") == "healthy"
        elif rule == "memory_below_threshold":
            checks[rule] = state.metrics.get("ram_pct", 100.0) < 90.0
        elif rule == "config_valid":
            checks[rule] = bool(state.signals.get("config_valid", False))
        elif rule == "source_patched":
            checks[rule] = bool(state.signals.get("source_patched", False))
        elif rule == "heartbeat_seen":
            checks[rule] = bool(state.signals.get("heartbeat_seen", False))
        elif rule == "fd_limit_raised":
            checks[rule] = int(state.signals.get("fd_limit", 0)) >= 4096
        elif rule == "health_probe_correct":
            checks[rule] = bool(state.signals.get("health_probe_correct", False))
        elif rule == "backoff_enabled":
            checks[rule] = bool(state.signals.get("backoff_enabled", False))
        elif rule == "human_notified":
            checks[rule] = state.human_notified
        elif rule == "logo_replaced":
            checks[rule] = "/fixture/app/static/logo.png" in state.changed_paths
        elif rule == "ui_text_updated":
            checks[rule] = "/fixture/app/templates/main.html" in state.changed_paths
        elif rule == "ui_copy_matches":
            content = state.files.get("/fixture/app/templates/main.html", "")
            checks[rule] = str(state.signals.get("ui_copy_expected", "")) in content
        elif rule == "ui_placeholders_preserved":
            checks[rule] = bool(state.signals.get("ui_placeholders_preserved", False))
        elif rule == "sql_rows_updated":
            checks[rule] = int(state.db.get("affected_rows", 0)) > 0
        elif rule == "report_generated":
            checks[rule] = bool(state.signals.get("report_generated", False))
        elif rule == "report_sections_valid":
            checks[rule] = bool(state.signals.get("report_sections_valid", False))
        elif rule == "report_counts_valid":
            checks[rule] = bool(state.signals.get("report_counts_valid", False))
        elif rule == "valid_json_recovered":
            checks[rule] = bool(state.signals.get("valid_json_recovered", False))
        elif rule == "task_continues":
            checks[rule] = bool(state.signals.get("valid_json_recovered", False) or state.service_restarted or state.human_notified)
        elif rule == "rotation_enabled":
            checks[rule] = bool(state.signals.get("rotation_enabled", False))
        else:
            checks[rule] = False
    return checks


def run_durability_validations(scenario: Scenario, state: WorldState) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for rule in scenario.expected.durability_validation:
        if rule == "retention_config_set":
            checks[rule] = bool(state.signals.get("retention_enabled", False))
        elif rule == "worker_config_persisted":
            checks[rule] = int(state.signals.get("worker_multiplier", 999)) <= 2
        elif rule == "config_valid":
            checks[rule] = bool(state.signals.get("config_valid", False))
        elif rule == "source_patched":
            checks[rule] = bool(state.signals.get("source_patched", False))
        elif rule == "rotation_enabled":
            checks[rule] = bool(state.signals.get("rotation_enabled", False))
        elif rule == "health_probe_correct":
            checks[rule] = bool(state.signals.get("health_probe_correct", False))
        elif rule == "backoff_enabled":
            checks[rule] = bool(state.signals.get("backoff_enabled", False))
        elif rule == "fd_limit_raised":
            checks[rule] = int(state.signals.get("fd_limit", 0)) >= 4096
        elif rule == "report_sections_valid":
            checks[rule] = bool(state.signals.get("report_sections_valid", False))
        elif rule == "repeat_fault_does_not_recur":
            if scenario.expected.subtype == "tmp_dir_full":
                checks[rule] = bool(state.signals.get("retention_enabled", False))
            elif scenario.expected.subtype == "cache_growth":
                checks[rule] = bool(state.signals.get("cache_trimmed", False))
            elif scenario.expected.subtype in {"inode_exhaustion", "inode_full"}:
                checks[rule] = bool(state.signals.get("retention_enabled", False))
            elif scenario.expected.subtype == "log_dir_full":
                checks[rule] = bool(state.signals.get("rotation_enabled", False))
            elif scenario.expected.problem_type == "resource.memory":
                checks[rule] = bool(state.signals.get("cache_trimmed", False) or state.signals.get("source_patched", False))
            else:
                checks[rule] = False
        elif rule == "escalated_with_evidence":
            checks[rule] = state.human_notified
        else:
            checks[rule] = False
    return checks


def run_regression_checks(scenario: Scenario, state: WorldState) -> dict[str, bool]:
    allowed = set(scenario.safety.allowed_paths)
    unexpected = [p for p in state.changed_paths if p not in allowed]
    api_pass = state.health.get("api") in {"healthy", "degraded"} if scenario.expected.escalation_expected else state.health.get("api") == "healthy"
    e2e_pass = api_pass
    no_unexpected_diff = len(unexpected) == 0
    return {
        "core_api_passes": api_pass,
        "e2e_passes": e2e_pass,
        "no_unexpected_diff": no_unexpected_diff,
        "unexpected_paths_count": len(unexpected),
    }
