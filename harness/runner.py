from __future__ import annotations

from pathlib import Path
import hashlib
import json
import statistics
import time
from typing import Any

from .agent_protocol import parse_decision, validate_decision_shape, decision_to_dict
from .baseline_agent import BaselineRuleAgent
from .llm_agent import LlamaJSONAgent
from .event_feed import WorldState, apply_round_event, iter_rounds
from .scenario_schema import Scenario, load_scenarios
from .scoring import RoundTrace, score_scenario
from .tools import execute_tool, run_durability_validations, run_fix_validations, run_regression_checks


def _scenario_trace_record(
    scenario: Scenario,
    round_idx: int,
    decision_payload: dict[str, Any],
    protocol_errors: list[str],
    tool_results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "scenario_id": scenario.id,
        "round": round_idx,
        "decision": decision_payload,
        "protocol_errors": protocol_errors,
        "tool_results": tool_results,
    }


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)[:96]


def _write_trace_artifact(
    *,
    trace_dir: Path,
    scenario: Scenario,
    round_idx: int,
    observation: dict[str, Any],
    decision_payload: dict[str, Any],
    protocol_errors: list[str],
    tool_results: list[dict[str, Any]],
    meta: dict[str, Any],
) -> str:
    trace_dir.mkdir(parents=True, exist_ok=True)
    raw = str(meta.get("raw_response", ""))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    path = trace_dir / f"{_safe_name(scenario.id)}__r{round_idx}__{digest}.json"
    artifact = {
        "scenario_id": scenario.id,
        "round": round_idx,
        "observation": observation,
        "decision": decision_payload,
        "protocol_errors": protocol_errors,
        "tool_results": tool_results,
        "agent_meta": meta,
        "trajectory_integrity": {
            "has_system_prompt": bool(meta.get("system_prompt")),
            "has_user_prompt": bool(meta.get("user_prompt")),
            "has_raw_response": "raw_response" in meta,
            "has_raw_content": "raw_content" in meta,
            "has_raw_reasoning_content": "raw_reasoning_content" in meta,
            "has_raw_api_response": bool(meta.get("raw_api_response")),
            "raw_sha256": digest,
        },
    }
    path.write_text(json.dumps(artifact, indent=2, ensure_ascii=True), encoding="utf-8")
    return str(path)


def run_benchmark(
    *,
    scenarios_dir: Path,
    output_path: Path,
    max_rounds: int | None = None,
    agent_mode: str = "baseline_rule",
    base_url: str | None = None,
    model: str | None = None,
    prompt_style: str = "strict_json",
    harness_profile: str = "llama_cpp_agent_style",
    tool_mode: str = "all",
    memory_mode: str = "none",
    timeout_s: float = 180.0,
    max_tokens: int = 220,
    recovery_mode: str = "heuristic",
    debug_prompts: bool = False,
    grammar_mode: str = "none",
    adapter_name: str = "baseline_rule",
    preserve_trace_artifacts: bool = True,
    trace_dir: Path | None = None,
) -> dict[str, Any]:
    started = time.time()
    scenarios = load_scenarios(scenarios_dir)
    if agent_mode == "baseline_rule":
        agent = BaselineRuleAgent()
    elif agent_mode == "llama_json":
        if not base_url or not model:
            raise ValueError("base_url and model are required for agent_mode=llama_json")
        agent = LlamaJSONAgent(
            base_url=base_url,
            model=model,
            prompt_style=prompt_style,
            harness_profile=harness_profile,
            tool_mode=tool_mode,
            memory_mode=memory_mode,
            timeout_s=timeout_s,
            max_tokens=max_tokens,
            recovery_mode=recovery_mode,
            debug_prompts=debug_prompts,
            grammar_mode=grammar_mode,
        )
    else:
        raise ValueError(f"unsupported agent_mode={agent_mode}")

    records: list[dict[str, Any]] = []
    by_scenario: dict[str, Any] = {}
    by_category_scores: dict[str, list[float]] = {}
    total_llm_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tool_calls = 0
    total_tool_failures = 0
    total_recoveries = 0
    total_malformed_outputs = 0
    total_parseable_outputs = 0
    total_compact_outputs = 0
    total_micro_outputs = 0
    total_micro_action_repairs = 0
    trace_artifacts: list[str] = []
    trace_root = trace_dir or output_path.with_suffix("").parent / f"{output_path.stem}_traces"

    for scenario in scenarios:
        state = WorldState.from_baseline(scenario.baseline_state)
        traces: list[RoundTrace] = []
        protocol_fail_count = 0
        if hasattr(agent, "reset_scenario"):
            agent.reset_scenario()

        rounds = iter_rounds(scenario)
        if max_rounds is not None:
            rounds = rounds[:max_rounds]

        for rnd in rounds:
            apply_round_event(state, rnd)
            observation = {
                "metrics": dict(state.metrics),
                "health": dict(state.health),
                "signals": dict(state.signals),
                "logs": list(state.logs),
            }
            if hasattr(agent, "decide_with_meta"):
                decision_obj, meta = agent.decide_with_meta(scenario, rnd.round, state)
            else:
                decision_obj = agent.decide(scenario, rnd.round, state)
                meta = {"llm_calls": 0, "input_tokens": 0, "output_tokens": 0}
            decision_payload = decision_to_dict(decision_obj)
            parsed = parse_decision(decision_payload)
            protocol_errors = validate_decision_shape(parsed)

            tool_results: list[dict[str, Any]] = []
            tool_failures = 0
            tool_names: list[str] = []
            allowed_tools = set(scenario.expected.allowed_actions)
            disallowed_tools = set(scenario.expected.disallowed_actions)
            if parsed.status == "ok":
                protocol_errors.extend(
                    f"action_not_allowed_for_ok:{action.tool}" for action in parsed.actions
                )
            protocol_errors.extend(
                f"unauthorized_tool:{action.tool}"
                for action in parsed.actions
                if action.tool not in allowed_tools or action.tool in disallowed_tools
            )
            decision_protocol_invalid = bool(protocol_errors)
            for action in parsed.actions:
                tool_names.append(action.tool)
                total_tool_calls += 1
                if decision_protocol_invalid:
                    tool_failures += 1
                    total_tool_failures += 1
                    tool_results.append(
                        {"tool": action.tool, "ok": False, "observation": {"error": "protocol_invalid"}}
                    )
                    continue
                result = execute_tool(tool=action.tool, args=action.args, state=state, scenario=scenario)
                if not result.ok:
                    tool_failures += 1
                    total_tool_failures += 1
                tool_results.append({"tool": action.tool, "ok": result.ok, "observation": result.observation})
            if protocol_errors:
                protocol_fail_count += 1

            total_llm_calls += int(meta.get("llm_calls", 0))
            total_input_tokens += int(meta.get("input_tokens", 0))
            total_output_tokens += int(meta.get("output_tokens", 0))
            if meta.get("malformed_output", False):
                total_malformed_outputs += 1
            if meta.get("recovery_applied", False):
                total_recoveries += 1
            if meta.get("model_payload_parseable", False):
                total_parseable_outputs += 1
            if meta.get("model_payload_was_compact", False):
                total_compact_outputs += 1
            if meta.get("model_payload_was_micro", False):
                total_micro_outputs += 1
            if meta.get("micro_action_repair_applied", False):
                total_micro_action_repairs += 1
            traces.append(
                RoundTrace(
                    round_idx=rnd.round,
                    decision=parsed,
                    protocol_errors=protocol_errors,
                    tool_calls=tool_names,
                    tool_failures=tool_failures,
                    malformed_output=bool(meta.get("malformed_output", False)),
                    recovery_applied=bool(meta.get("recovery_applied", False)),
                    micro_action_repair_applied=bool(meta.get("micro_action_repair_applied", False)),
                    model_payload_parseable=bool(meta.get("model_payload_parseable", True)),
                    model_emits_evidence=(
                        meta.get("prompt_style") not in {"micro_json", "compact_json"}
                        and not bool(meta.get("recovery_applied", False))
                    ),
                    observation=observation,
                )
            )
            rec = _scenario_trace_record(scenario, rnd.round, decision_payload, protocol_errors, tool_results)
            if meta:
                rec["agent_meta"] = meta
            if preserve_trace_artifacts:
                artifact_path = _write_trace_artifact(
                    trace_dir=trace_root,
                    scenario=scenario,
                    round_idx=rnd.round,
                    observation=observation,
                    decision_payload=decision_payload,
                    protocol_errors=protocol_errors,
                    tool_results=tool_results,
                    meta=meta,
                )
                rec["trajectory_artifact"] = artifact_path
                trace_artifacts.append(artifact_path)
            records.append(rec)

        fix_validation = run_fix_validations(scenario, state)
        durability_validation = run_durability_validations(scenario, state)
        regression = run_regression_checks(scenario, state)
        score = score_scenario(
            scenario=scenario,
            traces=traces,
            fix_validation=fix_validation,
            durability_validation=durability_validation,
            regression=regression,
            protocol_fail_count=protocol_fail_count,
        )

        by_scenario[scenario.id] = {
            "title": scenario.title,
            "category": scenario.category,
            "score": score.total,
            "raw_score": score.raw_score,
            "max_points": score.max_points,
            "breakdown": score.breakdown,
            "penalties": score.penalties,
            "caps": score.caps,
            "detected_round": score.detected_round,
            "max_score_class": scenario.max_score_class,
            "escalation_expected": scenario.expected.escalation_expected,
            "difficulty": {
                "detect": scenario.difficulty.detect,
                "temporary_fix": scenario.difficulty.temporary_fix,
                "permanent_fix": scenario.difficulty.permanent_fix,
                "regression_risk": scenario.difficulty.regression_risk,
                "edge_realism": scenario.difficulty.edge_realism,
            },
            "fix_validation": fix_validation,
            "durability_validation": durability_validation,
            "regression": regression,
            "protocol_fail_count": protocol_fail_count,
        }
        by_category_scores.setdefault(scenario.category, []).append(score.total)

    all_scores = [v["score"] for v in by_scenario.values()]
    detect_rounds = [v["detected_round"] for v in by_scenario.values() if v["detected_round"] is not None]

    summary = {
        "overall_score": round(statistics.mean(all_scores), 4) if all_scores else 0.0,
        "raw_overall_score": round(statistics.mean(v["raw_score"] for v in by_scenario.values()), 4) if by_scenario else 0.0,
        "overall_max_points": round(statistics.mean(v["max_points"] for v in by_scenario.values()), 4) if by_scenario else 0.0,
        "detection_score": round(statistics.mean(v["breakdown"]["detection"] for v in by_scenario.values()), 4) if by_scenario else 0.0,
        "analysis_score": round(statistics.mean(v["breakdown"]["diagnosis"] for v in by_scenario.values()), 4) if by_scenario else 0.0,
        "resolution_score": round(
            statistics.mean(
                0.50 * v["breakdown"]["action_strategy"]
                + 0.30 * v["breakdown"]["temporary_fix"]
                + 0.20 * v["breakdown"]["permanent_fix"]
                for v in by_scenario.values()
            ),
            4,
        ) if by_scenario else 0.0,
        "temporary_fix_score": round(statistics.mean(v["breakdown"]["temporary_fix"] for v in by_scenario.values()), 4) if by_scenario else 0.0,
        "permanent_fix_score": round(statistics.mean(v["breakdown"]["permanent_fix"] for v in by_scenario.values()), 4) if by_scenario else 0.0,
        "safety_score": round(statistics.mean(v["breakdown"]["safety"] for v in by_scenario.values()), 4) if by_scenario else 0.0,
        "communication_score": round(statistics.mean(v["breakdown"]["communication"] for v in by_scenario.values()), 4) if by_scenario else 0.0,
    }

    by_category = {
        k: {
            "mean_score": round(statistics.mean(vals), 4),
            "num_scenarios": len(vals),
        }
        for k, vals in by_category_scores.items()
    }

    result = {
        "config": {
            "agent_mode": agent_mode,
            "base_url": base_url,
            "model": model,
            "prompt_style": prompt_style,
            "harness_profile": harness_profile,
            "tool_mode": tool_mode,
            "memory_mode": memory_mode,
            "timeout_s": timeout_s,
            "max_tokens": max_tokens,
            "recovery_mode": recovery_mode,
            "debug_prompts": debug_prompts,
            "grammar_mode": grammar_mode,
            "adapter_name": adapter_name,
        },
        "summary": summary,
        "by_category": by_category,
        "by_scenario": by_scenario,
        "latency": {
            "mean_detect_round": round(statistics.mean(detect_rounds), 2) if detect_rounds else None,
            "p90_detect_round": _p90(detect_rounds) if detect_rounds else None,
            "mean_wall_time_s": round((time.time() - started) / max(1, len(scenarios)), 4),
        },
        "efficiency": {
            "mean_llm_calls": round(total_llm_calls / max(1, len(scenarios)), 2),
            "mean_tool_calls": round(total_tool_calls / max(1, len(scenarios)), 2),
            "failed_tool_calls": total_tool_failures,
            "mean_input_tokens": round(total_input_tokens / max(1, len(scenarios)), 2),
            "mean_output_tokens": round(total_output_tokens / max(1, len(scenarios)), 2),
            "malformed_output_count": total_malformed_outputs,
            "malformed_output_rate": round(total_malformed_outputs / max(1, total_llm_calls), 4) if total_llm_calls else 0.0,
            "parseable_output_count": total_parseable_outputs,
            "parseable_output_rate": round(total_parseable_outputs / max(1, total_llm_calls), 4) if total_llm_calls else 0.0,
            "compact_output_count": total_compact_outputs,
            "compact_output_rate": round(total_compact_outputs / max(1, total_llm_calls), 4) if total_llm_calls else 0.0,
            "micro_output_count": total_micro_outputs,
            "micro_output_rate": round(total_micro_outputs / max(1, total_llm_calls), 4) if total_llm_calls else 0.0,
            "recovery_count": total_recoveries,
            "recovery_rate": round(total_recoveries / max(1, total_llm_calls), 4) if total_llm_calls else 0.0,
            "micro_action_repair_count": total_micro_action_repairs,
            "micro_action_repair_rate": round(total_micro_action_repairs / max(1, total_llm_calls), 4) if total_llm_calls else 0.0,
            "model_independence_score": round(
                100.0 * (1.0 - ((total_recoveries + total_micro_action_repairs) / max(1, total_llm_calls))),
                2,
            ) if total_llm_calls else 100.0,
            "tokens_per_successful_fix": round(
                (total_input_tokens + total_output_tokens)
                / max(1, sum(1 for v in by_scenario.values() if v["score"] >= 0.70)),
                2,
            ),
        },
        "difficulty": _difficulty_breakdown(by_scenario),
        "safety_failures": _collect_safety_failures(by_scenario),
        "best_framework_model_prompt_memory": f"{harness_profile}|{model or 'n/a'}|{prompt_style}|{memory_mode}",
        "records": records,
        "trace_archive": {
            "enabled": preserve_trace_artifacts,
            "dir": str(trace_root) if preserve_trace_artifacts else None,
            "num_artifacts": len(trace_artifacts),
            "artifacts": trace_artifacts,
        },
        "runtime": {
            "duration_s": round(time.time() - started, 3),
            "num_scenarios": len(scenarios),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=True), encoding="utf-8")
    return result


def _collect_safety_failures(by_scenario: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for sid, row in by_scenario.items():
        if not row["regression"]["no_unexpected_diff"]:
            failures.append({"scenario_id": sid, "type": "unexpected_diff"})
        if not row["regression"]["core_api_passes"] and not row.get("escalation_expected", False):
            failures.append({"scenario_id": sid, "type": "core_api_failed_after_actions"})
    return failures


def _p90(values: list[int | None]) -> int | None:
    numeric = [x for x in values if isinstance(x, int)]
    if not numeric:
        return None
    ordered = sorted(numeric)
    idx = int((len(ordered) - 1) * 0.9)
    return ordered[idx]


def _difficulty_breakdown(by_scenario: dict[str, Any]) -> dict[str, Any]:
    buckets: dict[str, list[float]] = {}
    for row in by_scenario.values():
        d = row.get("difficulty", {})
        key = d.get("permanent_fix", "medium")
        buckets.setdefault(key, []).append(float(row["score"]))
    return {
        "permanent_fix": {k: round(sum(v) / len(v), 4) for k, v in buckets.items()},
    }


def inspect_benchmark_report(*, report_path: Path, scenarios_dir: Path | None = None) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    records = report.get("records", [])
    by_scenario = report.get("by_scenario", {})
    scenarios = {s.id: s for s in load_scenarios(scenarios_dir)} if scenarios_dir else {}

    trace_checks = {
        "records": len(records),
        "records_with_artifact": sum(1 for r in records if r.get("trajectory_artifact")),
        "records_with_raw_response": sum(1 for r in records if (r.get("agent_meta") or {}).get("raw_response") is not None),
        "records_with_reasoning": sum(1 for r in records if (r.get("agent_meta") or {}).get("raw_reasoning_content")),
        "records_with_raw_api_response": sum(1 for r in records if (r.get("agent_meta") or {}).get("raw_api_response")),
        "records_with_prompts": sum(1 for r in records if (r.get("agent_meta") or {}).get("system_prompt") and (r.get("agent_meta") or {}).get("user_prompt")),
    }

    scenario_findings: list[dict[str, Any]] = []
    for sid, row in sorted(by_scenario.items()):
        breakdown = row.get("breakdown", {})
        penalties = set(row.get("penalties", []))
        issues: list[str] = []
        recommendations: list[str] = []
        if breakdown.get("detection", 1.0) < 0.55 or "false_positive_before_fault" in penalties:
            issues.append("weak_or_early_detection")
            recommendations.append(
                "Prompt: decide from current metrics/logs/health/signals only; use ok+[] while observations are healthy; switch to suspect/incident only on objective fault evidence."
            )
        if breakdown.get("diagnosis", 1.0) < 0.65:
            issues.append("weak_diagnosis")
            recommendations.append(
                "Prompt: choose type/subtype/root labels or IDs by matching required evidence; do not reuse a familiar category when the evidence names another root cause."
            )
        if breakdown.get("action_strategy", 1.0) >= 0.75 and (
            breakdown.get("temporary_fix", 1.0) < 0.50 or breakdown.get("permanent_fix", 1.0) < 0.50
        ):
            issues.append("tools_chosen_but_fix_not_effective")
            recommendations.append(
                "Prompt: after diagnosing, include at least one state-changing allowed tool that matches the fault, not just diagnostics/restart."
            )
        if breakdown.get("safety", 1.0) < 0.60:
            issues.append("safety_or_regression_weak")
            recommendations.append("Prompt: avoid actions outside allowed paths/tools and prefer bounded reversible fixes before restart.")
        if row.get("detected_round") is None and row.get("score", 0.0) < 0.70:
            issues.append("never_marked_active")
            recommendations.append("Prompt: ok means no problem; if health is degraded, severe logs appear, or metrics cross thresholds, use suspect/incident.")
        scenario = scenarios.get(sid)
        if scenario:
            timing_notes = _scenario_timing_findings(scenario)
            if timing_notes:
                issues.append("scenario_timing_ambiguity")
                recommendations.extend(timing_notes)
        if issues:
            scenario_findings.append(
                {
                    "scenario_id": sid,
                    "score": row.get("score"),
                    "issues": issues,
                    "recommendations": recommendations,
                    "penalties": row.get("penalties", []),
                    "breakdown": breakdown,
                }
            )

    prompt_improvement_lines = _dedupe(
        rec
        for finding in scenario_findings
        for rec in finding["recommendations"]
        if rec.startswith("Prompt:")
    )
    scenario_improvement_lines = _dedupe(
        rec
        for finding in scenario_findings
        for rec in finding["recommendations"]
        if not rec.startswith("Prompt:")
    )

    return {
        "report": str(report_path),
        "summary": report.get("summary", {}),
        "trace_checks": trace_checks,
        "prompt_improvement_lines": prompt_improvement_lines,
        "scenario_or_scoring_improvements": scenario_improvement_lines,
        "scenario_findings": scenario_findings,
    }


def _dedupe(values: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def _scenario_timing_findings(scenario: Scenario) -> list[str]:
    findings: list[str] = []
    if scenario.fault_round > scenario.deadline_round:
        findings.append("Scenario: fault_round must be <= deadline_round.")
    if not scenario.rounds:
        findings.append("Scenario: add at least one explicit round event.")
    if scenario.fault_round > 0:
        state = WorldState.from_baseline(scenario.baseline_state)
        for rnd in iter_rounds(scenario):
            apply_round_event(state, rnd)
            if rnd.round >= scenario.fault_round:
                break
            logs = " ".join(state.logs[-5:]).lower()
            severe_log = any(token in logs for token in ("error", "traceback", "timeout", "enospc", "jsondecodeerror"))
            high_metric = any(state.metrics.get(k, 0) >= 90 for k in ("cpu_pct", "ram_pct", "disk_pct", "inode_pct"))
            degraded = state.health.get("api") not in {None, "healthy", "ok", "pass", "passing"}
            if severe_log or high_metric or degraded:
                findings.append("Scenario: move objective fault evidence out of pre-fault rounds or set fault_round earlier.")
                break
    return findings
