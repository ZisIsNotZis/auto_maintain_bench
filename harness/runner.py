from __future__ import annotations

from pathlib import Path
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
            if hasattr(agent, "decide_with_meta"):
                decision_obj, meta = agent.decide_with_meta(scenario, rnd.round, state)
            else:
                decision_obj = agent.decide(scenario, rnd.round, state)
                meta = {"llm_calls": 0, "input_tokens": 0, "output_tokens": 0}
            decision_payload = decision_to_dict(decision_obj)
            parsed = parse_decision(decision_payload)
            protocol_errors = validate_decision_shape(parsed)
            if protocol_errors:
                protocol_fail_count += 1

            tool_results: list[dict[str, Any]] = []
            tool_failures = 0
            tool_names: list[str] = []
            for action in parsed.actions:
                tool_names.append(action.tool)
                total_tool_calls += 1
                result = execute_tool(tool=action.tool, args=action.args, state=state, scenario=scenario)
                if not result.ok:
                    tool_failures += 1
                    total_tool_failures += 1
                tool_results.append({"tool": action.tool, "ok": result.ok, "observation": result.observation})

            total_llm_calls += int(meta.get("llm_calls", 0))
            total_input_tokens += int(meta.get("input_tokens", 0))
            total_output_tokens += int(meta.get("output_tokens", 0))
            if meta.get("malformed_output", False):
                total_malformed_outputs += 1
            if meta.get("recovery_applied", False):
                total_recoveries += 1
            traces.append(
                RoundTrace(
                    round_idx=rnd.round,
                    decision=parsed,
                    protocol_errors=protocol_errors,
                    tool_calls=tool_names,
                    tool_failures=tool_failures,
                )
            )
            rec = _scenario_trace_record(scenario, rnd.round, decision_payload, protocol_errors, tool_results)
            if meta:
                rec["agent_meta"] = meta
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
            "breakdown": score.breakdown,
            "penalties": score.penalties,
            "caps": score.caps,
            "detected_round": score.detected_round,
            "fix_validation": fix_validation,
            "durability_validation": durability_validation,
            "regression": regression,
            "protocol_fail_count": protocol_fail_count,
        }
        by_category_scores.setdefault(scenario.category, []).append(score.total)

    all_scores = [v["score"] for v in by_scenario.values()]
    detect_rounds = [v["detected_round"] for v in by_scenario.values() if v["detected_round"] is not None]

    summary = {
        "overall_score": round(statistics.mean(all_scores), 2) if all_scores else 0.0,
        "detection_score": round(statistics.mean(v["breakdown"]["detection"] + v["breakdown"]["detection_latency"] for v in by_scenario.values()), 2) if by_scenario else 0.0,
        "analysis_score": round(statistics.mean(v["breakdown"]["problem_type"] + v["breakdown"]["root_cause"] for v in by_scenario.values()), 2) if by_scenario else 0.0,
        "resolution_score": round(statistics.mean(v["breakdown"]["solution_selection"] + v["breakdown"]["fix_execution"] for v in by_scenario.values()), 2) if by_scenario else 0.0,
        "safety_score": round(statistics.mean(v["breakdown"]["regression_safety"] for v in by_scenario.values()), 2) if by_scenario else 0.0,
        "durability_score": round(statistics.mean(v["breakdown"]["durability"] + v["breakdown"]["escalation_quality"] for v in by_scenario.values()), 2) if by_scenario else 0.0,
    }

    by_category = {
        k: {
            "mean_score": round(statistics.mean(vals), 2),
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
            "recovery_count": total_recoveries,
            "recovery_rate": round(total_recoveries / max(1, total_llm_calls), 4) if total_llm_calls else 0.0,
            "tokens_per_successful_fix": round(
                (total_input_tokens + total_output_tokens)
                / max(1, sum(1 for v in by_scenario.values() if v["score"] >= 70.0)),
                2,
            ),
        },
        "safety_failures": _collect_safety_failures(by_scenario),
        "best_framework_model_prompt_memory": f"{harness_profile}|{model or 'n/a'}|{prompt_style}|{memory_mode}",
        "records": records,
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
        if not row["regression"]["core_api_passes"] and row["category"] != "escalation":
            failures.append({"scenario_id": sid, "type": "core_api_failed_after_actions"})
    return failures


def _p90(values: list[int | None]) -> int | None:
    numeric = [x for x in values if isinstance(x, int)]
    if not numeric:
        return None
    ordered = sorted(numeric)
    idx = int((len(ordered) - 1) * 0.9)
    return ordered[idx]
