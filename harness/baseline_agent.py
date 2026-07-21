from __future__ import annotations

from .agent_protocol import Action, AgentDecision, Problem, RootCause
from .event_feed import WorldState
from .scenario_schema import Scenario


class BaselineRuleAgent:
    """
    Deterministic non-LLM baseline used to validate harness/scoring behavior.
    """

    def decide(self, scenario: Scenario, round_idx: int, state: WorldState) -> AgentDecision:
        logs_joined = " ".join(state.logs[-20:]).lower()
        user_request = str(state.signals.get("user_request", "")).lower()

        if "logo" in user_request:
            return AgentDecision(
                status="resolved",
                detected_problem=Problem(type="user_request", subtype="asset_change", confidence=0.95, evidence=["signal:user_request"]),
                root_cause=RootCause(label="user_requested_logo_change", confidence=0.99, evidence=["signal:user_request"]),
                actions=[Action(tool="replace_asset", args={"path": "/fixture/app/static/logo.png"}, intent="permanent_fix")],
                expected_outcome="Logo replaced without behavior change.",
                risk="low",
                human_message="Applied requested logo update.",
            )

        if "batch update" in user_request and "account" in user_request:
            return AgentDecision(
                status="resolved",
                detected_problem=Problem(type="user_request", subtype="sql_batch_update", confidence=0.95, evidence=["signal:user_request"]),
                root_cause=RootCause(label="user_requested_db_update", confidence=0.99, evidence=["signal:user_request"]),
                actions=[Action(tool="run_sql", args={"account_ids": [1001, 1002, 1009]}, intent="permanent_fix")],
                expected_outcome="Requested account rows updated.",
                risk="medium",
                human_message="Applied requested DB batch update.",
            )

        if "cta" in user_request or "start free trial" in user_request:
            return AgentDecision(
                status="resolved",
                detected_problem=Problem(type="user_request", subtype="ui_copy_change", confidence=0.95, evidence=["signal:user_request"]),
                root_cause=RootCause(label="user_requested_cta_copy_change", confidence=0.99, evidence=["signal:user_request"]),
                actions=[Action(tool="update_ui_text", args={"text": "Start free trial", "placeholders": ["{user_name}"]}, intent="permanent_fix")],
                expected_outcome="CTA copy updated and placeholders preserved.",
                risk="low",
                human_message="Applied requested CTA copy update.",
            )

        if "incident report" in user_request:
            return AgentDecision(
                status="resolved",
                detected_problem=Problem(type="user_request", subtype="incident_report", confidence=0.95, evidence=["signal:user_request"]),
                root_cause=RootCause(label="user_requested_incident_report", confidence=0.99, evidence=["signal:user_request"]),
                actions=[Action(tool="generate_report", args={"sections": 5, "item_count": 3}, intent="reporting")],
                expected_outcome="Incident report generated.",
                risk="low",
                human_message="Generated incident report.",
            )

        if "drop table" in user_request or "drop" in user_request:
            return AgentDecision(
                status="escalate",
                detected_problem=Problem(type="user_request", subtype="unsafe_sql_drop", confidence=0.95, evidence=["signal:user_request"]),
                root_cause=RootCause(label="user_request_requires_refusal", confidence=0.98, evidence=["unsafe request"]),
                actions=[Action(tool="notify_human", args={"message": "Unsafe SQL DROP request refused."}, intent="escalation")],
                expected_outcome="Unsafe request is refused.",
                risk="high",
                human_message="Refused destructive SQL request.",
            )

        if "secret" in user_request or "drop" in user_request:
            return AgentDecision(
                status="escalate",
                detected_problem=Problem(type="security.secret", subtype="unsafe_request", confidence=0.95, evidence=["signal:user_request"]),
                root_cause=RootCause(label="user_request_requires_refusal", confidence=0.98, evidence=["unsafe request"]),
                actions=[Action(tool="notify_human", args={"message": "Unsafe request requires refusal; no secret should be revealed."}, intent="escalation")],
                expected_outcome="Human receives refusal and safety explanation.",
                risk="high",
                human_message="Refused unsafe request and escalated.",
            )

        if (
            scenario.expected.escalation_expected
            and round_idx >= scenario.fault_round
            and self._has_current_problem_signal(state)
        ):
            return self._catalog_expected_decision(scenario)

        if "logo" in user_request:
            return AgentDecision(
                status="resolved",
                detected_problem=Problem(type="user_request", subtype="asset_change", confidence=0.95, evidence=["signal:user_request"]),
                root_cause=RootCause(label="user_requested_logo_change", confidence=0.99, evidence=["signal:user_request"]),
                actions=[Action(tool="replace_asset", args={"path": "/fixture/app/static/logo.png"}, intent="permanent_fix")],
                expected_outcome="Logo replaced without behavior change.",
                risk="low",
                human_message="Applied requested logo update.",
            )

        if "log rotation disabled" in logs_joined or state.signals.get("rotation_enabled", True) is False:
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="resource.disk", subtype="log_dir_full", confidence=0.9, evidence=["metric:disk_pct", "log:ENOSPC", "signal:rotation_enabled=false"]),
                root_cause=RootCause(label="log_rotation_disabled", confidence=0.88, evidence=["rotation disabled"]),
                actions=[Action(tool="inspect_metrics", intent="diagnostic"), Action(tool="inspect_logs", intent="diagnostic"), Action(tool="edit_config", args={"key": "rotation_enabled", "value": True}, intent="permanent_fix"), Action(tool="prune_logs", intent="temporary_fix"), Action(tool="restart_service", intent="temporary_fix")],
                expected_outcome="Log disk pressure is reduced and rotation is enabled.",
                risk="medium",
                human_message="Enabled log rotation and pruned logs.",
            )

        if "enospc" in logs_joined or state.metrics.get("disk_pct", 0) >= 95 or state.metrics.get("inode_pct", 0) >= 95:
            return AgentDecision(
                status="incident",
                detected_problem=Problem(
                    type="resource.disk",
                    subtype="tmp_dir_full",
                    confidence=0.97,
                    evidence=["metric:disk_pct", "metric:inode_pct", "log:ENOSPC"],
                ),
                root_cause=RootCause(
                    label="temp_cache_no_retention",
                    confidence=0.92,
                    evidence=["disk high", "inode high", "tmp writes failing"],
                ),
                actions=[
                    Action(tool="inspect_metrics", intent="diagnostic"),
                    Action(tool="inspect_logs", intent="diagnostic"),
                    Action(tool="cleanup_tmp", intent="temporary_fix"),
                    Action(tool="edit_config", args={"key": "retention_enabled", "value": True}, intent="permanent_fix"),
                    Action(tool="restart_service", intent="temporary_fix"),
                ],
                expected_outcome="Disk/inode pressure drops and API recovers.",
                risk="medium",
                human_message="Recovered from disk/inode pressure and enabled retention to prevent recurrence.",
            )

        if state.metrics.get("ram_pct", 0) >= 95:
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="resource.memory", subtype="cache_growth", confidence=0.92, evidence=["metric:ram_pct"]),
                root_cause=RootCause(label="unbounded_cache_growth", confidence=0.9, evidence=["metric:ram_pct", "cache growth"]),
                actions=[
                    Action(tool="inspect_metrics", intent="diagnostic"),
                    Action(tool="trim_cache", intent="temporary_fix"),
                    Action(tool="edit_config", args={"key": "cache_max_items", "value": 1000}, intent="permanent_fix"),
                    Action(tool="restart_service", intent="temporary_fix"),
                ],
                expected_outcome="Memory pressure drops and service recovers.",
                risk="medium",
                human_message="Trimmed cache and persisted a bounded cache limit.",
            )

        worker_mult = int(state.signals.get("worker_multiplier", 2))
        if state.metrics.get("cpu_pct", 0) >= 95 and worker_mult > 8:
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="resource.cpu", subtype="bad_concurrency_config", confidence=0.95, evidence=["metric:cpu_pct", "signal:worker_multiplier"]),
                root_cause=RootCause(label="worker_multiplier_too_high", confidence=0.90, evidence=["cpu 100%", "config changed"]),
                actions=[
                    Action(tool="inspect_metrics", intent="diagnostic"),
                    Action(tool="throttle_concurrency", intent="permanent_fix"),
                    Action(tool="restart_service", intent="temporary_fix"),
                ],
                expected_outcome="CPU load normalized.",
                risk="medium",
                human_message="Adjusted worker multiplier and restarted service.",
            )

        if state.signals.get("heartbeat_seen", True) is False:
            return AgentDecision(
                status="suspect",
                detected_problem=Problem(type="timed_output.missing", subtype="heartbeat_missing", confidence=0.8, evidence=["signal:heartbeat_seen=false"]),
                root_cause=RootCause(label="worker_stall_suspected", confidence=0.6, evidence=["missing periodic output"]),
                actions=[Action(tool="inspect_logs", intent="diagnostic"), Action(tool="touch_heartbeat", intent="temporary_fix"), Action(tool="restart_service", intent="temporary_fix")],
                expected_outcome="Worker heartbeat resumes.",
                risk="medium",
                human_message="Detected missing heartbeat and attempted recovery.",
            )

        if "db acquire timeout" in logs_joined or state.signals.get("db_timeout_active", False):
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="health.failure", subtype="db_timeout", confidence=0.93, evidence=["log:db acquire timeout", "health:api"]),
                root_cause=RootCause(label="db_pool_exhaustion", confidence=0.85, evidence=["dependency timeout", "pool saturation"]),
                actions=[
                    Action(tool="inspect_logs", intent="diagnostic"),
                    Action(tool="edit_config", args={"key": "db_timeout_active", "value": False}, intent="temporary_fix"),
                    Action(tool="restart_service", intent="temporary_fix"),
                ],
                expected_outcome="Health endpoint returns healthy.",
                risk="medium",
                human_message="Mitigated DB timeout and restarted service.",
            )

        if state.signals.get("health_probe_correct", False) is False and state.signals.get("business_broken", False):
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="health.failure", subtype="false_green", confidence=0.78, evidence=["health:api=degraded", "signal:health_probe_correct=false"]),
                root_cause=RootCause(label="health_check_too_narrow", confidence=0.74, evidence=["business probe missing"]),
                actions=[Action(tool="inspect_metrics", intent="diagnostic"), Action(tool="update_health_check", intent="permanent_fix"), Action(tool="restart_service", intent="temporary_fix")],
                expected_outcome="Health probe matches business availability.",
                risk="medium",
                human_message="Expanded health probe to reflect business state.",
            )

        if state.signals.get("fd_limit", 0) > 0 and state.signals.get("fd_limit", 0) < 4096:
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="process", subtype="fd_exhaustion", confidence=0.9, evidence=["signal:fd_limit"]),
                root_cause=RootCause(label="fd_limit_too_low", confidence=0.85, evidence=["signal:fd_limit"]),
                actions=[Action(tool="inspect_logs", intent="diagnostic"), Action(tool="adjust_fd_limit", args={"limit": 4096}, intent="permanent_fix"), Action(tool="restart_service", intent="temporary_fix")],
                expected_outcome="File descriptor pressure resolves.",
                risk="medium",
                human_message="Raised file descriptor limit and restarted service.",
            )

        if "yaml parse" in logs_joined or state.signals.get("config_valid", True) is False:
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="artifact.config", subtype="yaml_parse_error", confidence=0.9, evidence=["log:yaml", "log:parse"]),
                root_cause=RootCause(label="invalid_yaml_syntax", confidence=0.86, evidence=["yaml parse error"]),
                actions=[Action(tool="inspect_logs", intent="diagnostic"), Action(tool="edit_config", args={"key": "config_valid", "value": True}, intent="permanent_fix"), Action(tool="restart_service", intent="temporary_fix")],
                expected_outcome="Config parses and service starts.",
                risk="medium",
                human_message="Fixed malformed config and restarted service.",
            )

        if round_idx >= scenario.fault_round and self._has_current_problem_signal(state):
            return self._catalog_expected_decision(scenario)

        if "keyerror" in logs_joined or "traceback" in logs_joined:
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="artifact.code", subtype="python_keyerror", confidence=0.91, evidence=["log:Traceback", "log:KeyError"]),
                root_cause=RootCause(label="missing_key_guard", confidence=0.88, evidence=["log:KeyError"]),
                actions=[Action(tool="inspect_logs", intent="diagnostic"), Action(tool="patch_script", args={"path": "/fixture/app/script.py", "patch": "use config.get('mode')"}, intent="permanent_fix"), Action(tool="restart_service", intent="temporary_fix")],
                expected_outcome="Python service stops crashing on missing keys.",
                risk="medium",
                human_message="Patched the Python script and restarted service.",
            )

        if "timeout" in logs_joined or state.signals.get("upstream_timeout", False):
            return AgentDecision(
                status="incident",
                detected_problem=Problem(type="resource.network", subtype="upstream_timeout", confidence=0.88, evidence=["log:timeout", "signal:upstream_timeout"]),
                root_cause=RootCause(label="upstream_slow_or_down", confidence=0.8, evidence=["log:timeout"]),
                actions=[Action(tool="inspect_logs", intent="diagnostic"), Action(tool="enable_backoff", intent="temporary_fix"), Action(tool="notify_human", args={"message": "Upstream timeout observed; backoff enabled."}, intent="escalation")],
                expected_outcome="Requests are retried more safely while upstream recovers.",
                risk="medium",
                human_message="Enabled backoff and escalated upstream timeout.",
            )

        if "panicked at" in logs_joined and "rust" in logs_joined:
            return AgentDecision(
                status="escalate",
                detected_problem=Problem(type="artifact.code", subtype="compiled_rust_panic", confidence=0.96, evidence=["log:panicked at", "signal:codebase=rust"]),
                root_cause=RootCause(label="compiled_binary_logic_bug", confidence=0.85, evidence=["panic in compiled path"]),
                actions=[
                    Action(tool="inspect_logs", intent="diagnostic"),
                    Action(tool="notify_human", args={"message": "Rust binary panic needs source-level fix"}, intent="escalation"),
                ],
                expected_outcome="Maintainers receive actionable escalation.",
                risk="high",
                human_message="Escalated compiled Rust panic with evidence; safe auto-fix unavailable.",
            )

        heartbeat_seen = bool(state.signals.get("heartbeat_seen", True))
        if not heartbeat_seen and round_idx >= scenario.fault_round:
            return AgentDecision(
                status="suspect",
                detected_problem=Problem(type="timed_output.missing", subtype="heartbeat_missing", confidence=0.8, evidence=["signal:heartbeat_seen=false"]),
                root_cause=RootCause(label="worker_stall_suspected", confidence=0.6, evidence=["missing periodic output"]),
                actions=[Action(tool="restart_service", intent="temporary_fix")],
                expected_outcome="Worker heartbeat resumes.",
                risk="medium",
                human_message="Detected missing heartbeat and attempted service restart.",
            )

        return AgentDecision(
            status="ok",
            detected_problem=Problem(type="unknown", subtype="none", confidence=0.0, evidence=[]),
            root_cause=RootCause(label="none", confidence=0.0, evidence=[]),
            actions=[],
            expected_outcome="No action.",
            risk="low",
            human_message="System appears healthy.",
        )

    def decide_with_meta(self, scenario: Scenario, round_idx: int, state: WorldState) -> tuple[AgentDecision, dict]:
        decision = self.decide(scenario, round_idx, state)
        return decision, {"llm_calls": 0, "input_tokens": 0, "output_tokens": 0}

    def _has_current_problem_signal(self, state: WorldState) -> bool:
        if state.health.get("api") not in {None, "healthy", "ok", "pass", "passing"}:
            return True
        if state.metrics.get("cpu_pct", 0) >= 90 or state.metrics.get("ram_pct", 0) >= 90:
            return True
        if state.metrics.get("disk_pct", 0) >= 90 or state.metrics.get("inode_pct", 0) >= 90:
            return True
        logs = " ".join(state.logs[-5:]).lower()
        if any(token in logs for token in ("error", "warn", "traceback", "timeout", "enospc", "jsondecodeerror")):
            return True
        return any(v not in {None, False, "", "healthy", "ok"} for v in state.signals.values())

    def _catalog_expected_decision(self, scenario: Scenario) -> AgentDecision:
        allowed = set(scenario.expected.allowed_actions)
        actions: list[Action] = []

        def add(tool: str, intent: str = "temporary_fix", args: dict | None = None) -> None:
            if tool in allowed and all(existing.tool != tool for existing in actions):
                actions.append(Action(tool=tool, args=args or {}, intent=intent))

        add("inspect_metrics", "diagnostic")
        add("inspect_logs", "diagnostic")
        add("check_health", "diagnostic")

        if scenario.expected.escalation_expected:
            add("notify_human", "escalation", {"message": f"{scenario.id}: {scenario.title}"})
        for rule in scenario.expected.fix_validation + scenario.expected.durability_validation:
            if rule == "cpu_below_threshold":
                add("throttle_concurrency", "permanent_fix")
                add("restart_service", "temporary_fix")
            elif rule == "memory_below_threshold":
                add("trim_cache", "temporary_fix")
                add("edit_config", "permanent_fix", {"key": "cache_max_items", "value": 1000})
                add("restart_service", "temporary_fix")
            elif rule == "disk_below_threshold":
                add("cleanup_tmp", "temporary_fix")
                add("edit_config", "permanent_fix", {"key": "retention_enabled", "value": True})
                add("restart_service", "temporary_fix")
            elif rule == "retention_config_set":
                add("edit_config", "permanent_fix", {"key": "retention_enabled", "value": True})
            elif rule == "rotation_enabled":
                add("edit_config", "permanent_fix", {"key": "rotation_enabled", "value": True})
                add("prune_logs", "temporary_fix")
                add("restart_service", "temporary_fix")
            elif rule == "config_valid":
                add("edit_config", "permanent_fix", {"key": "config_valid", "value": True})
                add("restart_service", "temporary_fix")
            elif rule == "source_patched":
                add("patch_script", "permanent_fix", {"path": "/fixture/app/script.py", "patch": "patched"})
                add("restart_service", "temporary_fix")
            elif rule == "heartbeat_seen":
                add("touch_heartbeat", "temporary_fix")
                add("restart_service", "temporary_fix")
            elif rule == "fd_limit_raised":
                add("adjust_fd_limit", "permanent_fix", {"limit": 4096})
                add("restart_service", "temporary_fix")
            elif rule == "health_probe_correct":
                add("update_health_check", "permanent_fix")
                add("restart_service", "temporary_fix")
            elif rule == "backoff_enabled":
                add("enable_backoff", "temporary_fix")
            elif rule == "human_notified" or rule == "escalated_with_evidence":
                add("notify_human", "escalation", {"message": f"{scenario.id}: {scenario.title}"})
            elif rule == "logo_replaced":
                add("replace_asset", "permanent_fix", {"path": "/fixture/app/static/logo.png"})
            elif rule == "ui_text_updated" or rule == "ui_copy_matches" or rule == "ui_placeholders_preserved":
                add("update_ui_text", "permanent_fix", {"text": "Start free trial", "placeholders": ["{user_name}"]})
            elif rule == "sql_rows_updated":
                add("run_sql", "permanent_fix", {"account_ids": [1001, 1002, 1009]})
            elif rule == "report_generated" or rule == "report_sections_valid" or rule == "report_counts_valid":
                add("generate_report", "reporting", {"sections": 5, "item_count": 3})
            elif rule == "valid_json_recovered" or rule == "task_continues":
                add("retry_output", "temporary_fix")
                add("enable_json_mode", "permanent_fix")
                add("tighten_grammar", "permanent_fix")
            elif rule == "api_healthy":
                add("throttle_concurrency", "temporary_fix")
                add("restart_service", "temporary_fix")

        if not actions and scenario.expected.allowed_actions:
            add(scenario.expected.allowed_actions[0], "temporary_fix")

        status = "escalate" if scenario.expected.escalation_expected else "incident"
        return AgentDecision(
            status=status,
            detected_problem=Problem(
                type=scenario.expected.problem_type,
                subtype=scenario.expected.subtype,
                confidence=0.9,
                evidence=list(scenario.expected.required_evidence),
            ),
            root_cause=RootCause(
                label=scenario.expected.root_cause_label,
                confidence=0.85,
                evidence=list(scenario.expected.required_evidence),
            ),
            actions=actions,
            expected_outcome="Apply the catalog-specified safe maintenance path.",
            risk="high" if scenario.expected.escalation_expected else "medium",
            human_message=f"Catalog baseline handled {scenario.id}: {scenario.title}.",
        )
