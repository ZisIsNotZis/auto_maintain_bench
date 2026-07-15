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
