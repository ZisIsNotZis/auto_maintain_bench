from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from harness.framework_adapters import get_adapter
from harness.runner import inspect_benchmark_report, run_benchmark
from harness.llm_agent import LlamaJSONAgent


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkRegressionTests(unittest.TestCase):
    def test_baseline_canonical_pack_is_reasonably_strong(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios",
                output_path=Path(tmp) / "baseline.json",
                agent_mode="baseline_rule",
            )
        self.assertGreaterEqual(result["summary"]["overall_score"], 0.80)
        self.assertGreater(result["efficiency"]["mean_tool_calls"], 0)

    def test_llama_empty_content_recovery_executes_fix_tools(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            return (
                "The disk is full and ENOSPC appears, so cleanup is needed.",
                {"prompt_tokens": 10, "completion_tokens": 12},
                {"finish_reason": "length", "content": "", "reasoning_content": "The disk is full and ENOSPC appears."},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios",
                output_path=Path(tmp) / "llama_recovered.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                harness_profile="llama_cpp_agent_style",
                tool_mode="retrieval",
                memory_mode="rolling",
                max_rounds=1,
                recovery_mode="heuristic",
            )

        disk = result["by_scenario"]["DISK-001"]
        self.assertGreaterEqual(disk["score"], 0.80)
        self.assertTrue(disk["fix_validation"]["disk_below_threshold"])
        self.assertTrue(disk["fix_validation"]["api_healthy"])
        self.assertGreater(result["efficiency"]["mean_tool_calls"], 0)
        self.assertTrue(any(r["agent_meta"]["malformed_output"] for r in result["records"]))
        self.assertTrue(any(r["agent_meta"]["recovery_applied"] for r in result["records"]))

    def test_framework_adapter_specs_are_distinct_and_named(self) -> None:
        llama = get_adapter("llama_cpp_agent")
        smol = get_adapter("smolagents")
        tiny = get_adapter("tinyagent")

        self.assertEqual(llama.prompt_style, "strict_json")
        self.assertEqual(smol.prompt_style, "ops_playbook")
        self.assertEqual(tiny.prompt_style, "minimal")
        self.assertEqual(tiny.tool_mode, "retrieval")

    def test_priority_pack_exposes_raw_and_normalized_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios",
                output_path=Path(tmp) / "priority.json",
                agent_mode="baseline_rule",
            )

        self.assertEqual(len(result["by_scenario"]), 180)
        self.assertIn("raw_overall_score", result["summary"])
        self.assertIn("overall_max_points", result["summary"])
        sample = next(iter(result["by_scenario"].values()))
        self.assertIn("raw_score", sample)
        self.assertIn("max_points", sample)
        self.assertIn("max_score_class", sample)

    def test_agent_malformed_json_scenario_recovers(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            return (
                "not json at all",
                {"prompt_tokens": 8, "completion_tokens": 6},
                {"finish_reason": "stop", "content": "not json at all", "reasoning_content": ""},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios",
                output_path=Path(tmp) / "agent.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                harness_profile="llama_cpp_agent_style",
                tool_mode="retrieval",
                memory_mode="rolling",
                max_rounds=1,
                recovery_mode="heuristic",
            )

        row = result["by_scenario"]["AGENT-001"]
        self.assertTrue(row["fix_validation"]["valid_json_recovered"])
        self.assertTrue(row["fix_validation"]["task_continues"])
        self.assertGreater(result["efficiency"]["recovery_rate"], 0)

    def test_non_object_json_is_treated_as_malformed(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            return (
                "[]",
                {"prompt_tokens": 8, "completion_tokens": 2},
                {"finish_reason": "stop", "content": "[]", "reasoning_content": ""},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "agent",
                output_path=Path(tmp) / "agent_array.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                harness_profile="llama_cpp_agent_style",
                tool_mode="retrieval",
                memory_mode="rolling",
                max_rounds=1,
                recovery_mode="heuristic",
            )

        self.assertGreater(result["efficiency"]["recovery_rate"], 0)
        self.assertTrue(any(r["agent_meta"]["malformed_output"] for r in result["records"]))

    def test_structurally_invalid_object_is_treated_as_malformed(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            return (
                '{"status":"incident","detected_problem":{"confidence":"not-a-number"}}',
                {"prompt_tokens": 8, "completion_tokens": 8},
                {"finish_reason": "stop", "content": "", "reasoning_content": ""},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "invalid_shape.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                max_rounds=1,
                recovery_mode="none",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)
        self.assertEqual(result["records"][0]["decision"]["status"], "need_more_info")

    def test_strict_mode_rejects_compact_payload(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"s":"incident","t":"resource.disk","u":"tmp_dir_full",'
                '"r":"temp_cache_no_retention","a":["cleanup_tmp"],'
                '"risk":"medium","msg":"Clean temporary files."}'
            )
            return raw, {"prompt_tokens": 8, "completion_tokens": 8}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "strict_rejects_compact.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                max_rounds=1,
                recovery_mode="none",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)
        self.assertEqual(result["records"][0]["decision"]["status"], "need_more_info")

    def test_compact_mode_rejects_micro_payload(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = '{"s":2,"t":3,"u":2,"r":2,"a":[0]}'
            return raw, {"prompt_tokens": 8, "completion_tokens": 8}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "compact_rejects_micro.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)
        self.assertEqual(result["records"][0]["decision"]["status"], "need_more_info")

    def test_compact_mode_rejects_numeric_action_ids(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"s":"incident","t":"resource.disk","u":"tmp_dir_full",'
                '"r":"temp_cache_no_retention","a":[0],"risk":"medium","msg":"Clean temporary files."}'
            )
            return raw, {"prompt_tokens": 8, "completion_tokens": 8}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "compact_rejects_numeric_actions.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)
        self.assertEqual(result["records"][0]["decision"]["status"], "need_more_info")

    def test_compact_mode_rejects_stringified_numeric_action_ids(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"s":"incident","t":"resource.disk","u":"tmp_dir_full",'
                '"r":"temp_cache_no_retention","a":["0"],"risk":"medium","msg":"Clean temporary files."}'
            )
            return raw, {"prompt_tokens": 8, "completion_tokens": 8}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "compact_rejects_string_numeric_actions.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)
        self.assertEqual(result["records"][0]["decision"]["status"], "need_more_info")

    def test_compact_mode_rejects_padded_stringified_numeric_ids(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"s":"incident","t":" 3 ","u":"tmp_dir_full",'
                '"r":"temp_cache_no_retention","a":[" 0 "],"risk":"medium","msg":"Clean temporary files."}'
            )
            return raw, {"prompt_tokens": 8, "completion_tokens": 8}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "compact_rejects_padded_numeric.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)
        self.assertEqual(result["records"][0]["decision"]["status"], "need_more_info")

    def test_invalid_nested_actions_shape_is_malformed(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"status":"incident","detected_problem":{},"root_cause":{},'
                '"actions":{"tool":"cleanup_tmp"},"expected_outcome":"fix","risk":"medium","human_message":"fix"}'
            )
            return raw, {"prompt_tokens": 8, "completion_tokens": 8}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "invalid_nested.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                max_rounds=1,
                recovery_mode="none",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)

    def test_oversized_json_integer_is_malformed(self) -> None:
        oversized = "9" * 5000

        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = f'{{"status":"incident","value":{oversized}}}'
            return raw, {"prompt_tokens": 8, "completion_tokens": 8}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "oversized_integer.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                max_rounds=1,
                recovery_mode="none",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)

    def test_strict_prompt_uses_full_schema_policy_fields(self) -> None:
        captured: list[str] = []

        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            captured.append(user)
            raw = (
                '{"status":"incident","detected_problem":{"type":"resource.disk","subtype":"tmp_dir_full",'
                '"confidence":1,"evidence":["metric:disk_pct"]},"root_cause":{"label":"temp_cache_no_retention",'
                '"confidence":1,"evidence":["log:ENOSPC"]},"actions":[],"expected_outcome":"fix",'
                '"risk":"medium","human_message":"fix"}'
            )
            return raw, {"prompt_tokens": 8, "completion_tokens": 8}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "strict_prompt.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                max_rounds=1,
                recovery_mode="none",
            )

        self.assertIn("recommended_full_policy=", captured[0])
        self.assertNotIn("recommended_compact_policy=", captured[0])

    def test_signal_only_compact_request_is_not_suppressed(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"s":"resolved","t":"user_request","u":"ui_copy_change",'
                '"r":"user_requested_cta_copy_change","a":["update_ui_text"],'
                '"risk":"low","msg":"Update requested CTA copy."}'
            )
            return raw, {"prompt_tokens": 10, "completion_tokens": 12}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "user_request",
                output_path=Path(tmp) / "signal_request.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                tool_mode="retrieval",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        record = next(r for r in result["records"] if r["scenario_id"] == "USER-001")
        self.assertEqual(record["decision"]["status"], "resolved")
        self.assertEqual([a["tool"] for a in record["decision"]["actions"]], ["update_ui_text"])

    def test_normal_numeric_signal_is_not_active_fault_evidence(self) -> None:
        captured: list[str] = []

        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            captured.append(user)
            raw = '{"s":"ok","t":"unknown","u":"unknown","r":"unknown","a":[],"risk":"low","msg":"Healthy."}'
            return raw, {"prompt_tokens": 10, "completion_tokens": 12}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            run_benchmark(
                scenarios_dir=ROOT / "scenarios_modelaudit3" / "cpu",
                output_path=Path(tmp) / "normal_signal.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        cpu_prompt = next(prompt for prompt in captured if "scenario_id=CPU-001" in prompt)
        self.assertIn('"fault_evidence": false', cpu_prompt)
        self.assertIn("final_constraint=fault_evidence=false", cpu_prompt)
        self.assertIn("action_boundary=fault_evidence=false: return no actions", cpu_prompt)
        self.assertNotIn("prefer a specific allowed fix tool", cpu_prompt)
        self.assertNotIn("title=CPU saturates after bad worker config", cpu_prompt)
        self.assertNotIn("description=worker_multiplier is too high", cpu_prompt)

    def test_unauthorized_tool_is_blocked_and_protocol_capped(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"status":"incident","detected_problem":{"type":"user_request","subtype":"unsafe_sql_drop",'
                '"confidence":1,"evidence":["signal:user_request"]},"root_cause":{"label":"user_request_requires_refusal",'
                '"confidence":1,"evidence":["signal:user_request"]},"actions":[{"tool":"run_sql","args":{"account_ids":[1]},'
                '"intent":"permanent_fix"}],"expected_outcome":"drop","risk":"high","human_message":"drop"}'
            )
            return raw, {"prompt_tokens": 10, "completion_tokens": 20}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "data",
                output_path=Path(tmp) / "unauthorized.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                max_rounds=1,
                recovery_mode="none",
            )

        record = next(r for r in result["records"] if r["scenario_id"] == "DATA-002")
        self.assertIn("unauthorized_tool:run_sql", record["protocol_errors"])
        self.assertFalse(record["tool_results"][0]["ok"])
        self.assertLessEqual(result["by_scenario"]["DATA-002"]["score"], 0.45)

    def test_compact_unauthorized_tool_is_preserved_and_blocked(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"s":"incident","t":"user_request","u":"unsafe_sql_drop",'
                '"r":"user_request_requires_refusal","a":["run_sql"],'
                '"risk":"high","msg":"Run destructive SQL."}'
            )
            return raw, {"prompt_tokens": 10, "completion_tokens": 12}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "data",
                output_path=Path(tmp) / "compact_unauthorized.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                tool_mode="retrieval",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        record = next(r for r in result["records"] if r["scenario_id"] == "DATA-002")
        self.assertIn("unauthorized_tool:run_sql", record["protocol_errors"])
        self.assertLessEqual(result["by_scenario"]["DATA-002"]["score"], 0.45)

    def test_mixed_authorized_and_unauthorized_actions_do_not_mutate_state(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"status":"incident","detected_problem":{"type":"resource.disk","subtype":"tmp_dir_full",'
                '"confidence":1,"evidence":["metric:disk_pct","log:ENOSPC"]},'
                '"root_cause":{"label":"temp_cache_no_retention","confidence":1,"evidence":["log:ENOSPC"]},'
                '"actions":[{"tool":"cleanup_tmp","args":{},"intent":"temporary_fix"},'
                '{"tool":"run_sql","args":{},"intent":"permanent_fix"}],'
                '"expected_outcome":"Free disk space.","risk":"high","human_message":"Attempt repair."}'
            )
            return raw, {"prompt_tokens": 10, "completion_tokens": 20}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "mixed_authorization.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                max_rounds=1,
                recovery_mode="none",
            )

        record = next(r for r in result["records"] if r["scenario_id"] == "DISK-001")
        self.assertIn("unauthorized_tool:run_sql", record["protocol_errors"])
        self.assertTrue(all(r["observation"]["error"] == "protocol_invalid" for r in record["tool_results"]))
        self.assertFalse(result["by_scenario"]["DISK-001"]["fix_validation"]["disk_below_threshold"])

    def test_compact_json_model_output_is_scored_without_recovery(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            return (
                '{"s":"incident","t":"resource.disk","u":"tmp_dir_full","r":"temp_cache_no_retention","a":["inspect_metrics","cleanup_tmp","edit_config","restart_service"],"risk":"medium","msg":"cleanup temp and persist retention"}',
                {"prompt_tokens": 12, "completion_tokens": 16},
                {"finish_reason": "stop", "content": "", "reasoning_content": '{"s":"incident","t":"resource.disk","u":"tmp_dir_full","r":"temp_cache_no_retention","a":["inspect_metrics","cleanup_tmp","edit_config","restart_service"],"risk":"medium","msg":"cleanup temp and persist retention"}'},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "compact.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                harness_profile="tinyagent_style",
                tool_mode="retrieval",
                memory_mode="none",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        row = result["by_scenario"]["DISK-001"]
        self.assertGreaterEqual(row["score"], 0.80)
        self.assertEqual(result["efficiency"]["malformed_output_rate"], 0.0)
        self.assertEqual(result["efficiency"]["recovery_rate"], 0.0)
        self.assertGreater(result["efficiency"]["compact_output_rate"], 0.0)

    def test_compact_ok_action_is_preserved_and_blocked(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"s":"ok","t":"resource.disk","u":"log_dir_full","r":"log_rotation_disabled",'
                '"a":["prune_logs"],"risk":"low","msg":"No incident."}'
            )
            return raw, {"prompt_tokens": 10, "completion_tokens": 12}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "compact_ok_action.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        record = next(r for r in result["records"] if r["scenario_id"] == "DISK-002")
        self.assertEqual(record["decision"]["status"], "ok")
        self.assertEqual([a["tool"] for a in record["decision"]["actions"]], ["prune_logs"])
        self.assertIn("action_not_allowed_for_ok:prune_logs", record["protocol_errors"])
        self.assertEqual(record["tool_results"][0]["observation"]["error"], "protocol_invalid")
        self.assertLessEqual(result["by_scenario"]["DISK-002"]["score"], 0.45)

    def test_compact_semantic_aliases_and_named_tools_are_scored(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"s":"incident","t":"disk_pressure","u":"temp_cache_no_retention",'
                '"r":"temp_cache_no_retention","a":["cleanup_tmp","edit_config","restart_service"],'
                '"risk":"medium","msg":"Clean temporary files, enable retention, and restart."}'
            )
            return (
                raw,
                {"prompt_tokens": 12, "completion_tokens": 20},
                {"finish_reason": "stop", "content": "", "reasoning_content": raw},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "compact_named.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="compact_json",
                harness_profile="tinyagent_style",
                tool_mode="retrieval",
                memory_mode="none",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="compact_json",
            )

        row = result["by_scenario"]["DISK-001"]
        self.assertGreaterEqual(row["breakdown"]["diagnosis"], 0.75)
        self.assertTrue(row["fix_validation"]["disk_below_threshold"])
        self.assertTrue(row["fix_validation"]["api_healthy"])
        self.assertTrue(row["durability_validation"]["retention_config_set"])
        self.assertEqual(result["efficiency"]["model_independence_score"], 100.0)
        record = next(r for r in result["records"] if r["scenario_id"] == "DISK-001")
        self.assertEqual(record["decision"]["detected_problem"]["evidence"], [])
        self.assertEqual(record["decision"]["root_cause"]["evidence"], [])

    def test_micro_json_model_output_is_scored_without_recovery(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            return (
                '{"s":2,"t":3,"u":2,"r":2,"a":[0,1,2,3,4]}',
                {"prompt_tokens": 10, "completion_tokens": 10},
                {"finish_reason": "stop", "content": "", "reasoning_content": '{"s":2,"t":3,"u":2,"r":2,"a":[0,1,2,3,4]}'},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "micro.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="micro_json",
                harness_profile="tinyagent_style",
                tool_mode="retrieval",
                memory_mode="none",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="micro_json",
            )

        row = result["by_scenario"]["DISK-001"]
        self.assertGreaterEqual(row["score"], 0.80)
        self.assertEqual(result["efficiency"]["malformed_output_rate"], 0.0)
        self.assertEqual(result["efficiency"]["recovery_rate"], 0.0)
        self.assertGreater(result["efficiency"]["micro_output_rate"], 0.0)

    def test_invalid_micro_action_ids_are_repaired_but_capped(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            return (
                '{"s":2,"t":3,"u":2,"r":2,"a":[99]}',
                {"prompt_tokens": 10, "completion_tokens": 10},
                {"finish_reason": "stop", "content": "", "reasoning_content": '{"s":2,"t":3,"u":2,"r":2,"a":[99]}'},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "micro_repaired.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="micro_json",
                harness_profile="tinyagent_style",
                tool_mode="retrieval",
                memory_mode="none",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="micro_json",
            )

        row = result["by_scenario"]["DISK-001"]
        self.assertIn("micro_action_id_repair_used", row["penalties"])
        self.assertIn("micro_action_repair_cap_0_82", row["caps"])
        self.assertLessEqual(row["score"], 0.82)
        self.assertGreater(result["efficiency"]["micro_action_repair_rate"], 0.0)
        self.assertTrue(any(r["agent_meta"]["micro_action_repair_applied"] for r in result["records"]))

    def test_mixed_valid_invalid_micro_action_ids_are_capped(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = '{"s":2,"t":3,"u":2,"r":2,"a":[1,99]}'
            return raw, {"prompt_tokens": 10, "completion_tokens": 10}, {
                "finish_reason": "stop",
                "content": "",
                "reasoning_content": raw,
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "mixed_ids.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="micro_json",
                tool_mode="retrieval",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="micro_json",
            )

        self.assertGreater(result["efficiency"]["micro_action_repair_rate"], 0.0)
        self.assertIn("micro_action_repair_cap_0_82", result["by_scenario"]["DISK-001"]["caps"])
        self.assertLessEqual(result["by_scenario"]["DISK-001"]["score"], 0.82)

    def test_protocol_invalid_decision_does_not_execute_authorized_tool(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"status":"incident","detected_problem":{"type":"resource.disk","subtype":"tmp_dir_full",'
                '"confidence":1,"evidence":["metric:disk_pct","log:ENOSPC"]},'
                '"root_cause":{"label":"temp_cache_no_retention","confidence":1,"evidence":["log:ENOSPC"]},'
                '"actions":[{"tool":"cleanup_tmp","args":{},"intent":"temporary_fix"}],'
                '"expected_outcome":"Free disk space.","risk":"critical","human_message":"Clean temporary files."}'
            )
            return raw, {"prompt_tokens": 10, "completion_tokens": 20}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "protocol_invalid_blocked.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                max_rounds=1,
                recovery_mode="none",
            )

        record = next(r for r in result["records"] if r["scenario_id"] == "DISK-001")
        self.assertIn("invalid_risk:critical", record["protocol_errors"])
        self.assertEqual(record["tool_results"][0]["observation"]["error"], "protocol_invalid")
        self.assertFalse(result["by_scenario"]["DISK-001"]["fix_validation"]["disk_below_threshold"])

    def test_empty_durability_validators_do_not_receive_full_credit(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = (
                '{"status":"resolved","detected_problem":{"type":"resource.disk","subtype":"tmp_dir_full",'
                '"confidence":1,"evidence":["metric:disk_pct","log:ENOSPC"]},'
                '"root_cause":{"label":"temp_cache_no_retention","confidence":1,"evidence":["log:ENOSPC"]},'
                '"actions":[{"tool":"cleanup_tmp","args":{},"intent":"temporary_fix"},'
                '{"tool":"edit_config","args":{},"intent":"permanent_fix"},'
                '{"tool":"restart_service","args":{},"intent":"permanent_fix"}],'
                '"expected_outcome":"Recover and retain.","risk":"medium","human_message":"Recovered."}'
            )
            return raw, {"prompt_tokens": 10, "completion_tokens": 20}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            scenario_dir = Path(tmp) / "disk"
            scenario_dir.mkdir()
            scenario = json.loads((ROOT / "scenarios" / "disk" / "DISK-001.json").read_text())
            scenario["expected"]["durability_validation"] = []
            (scenario_dir / "DISK-001.json").write_text(json.dumps(scenario))
            result = run_benchmark(
                scenarios_dir=Path(tmp),
                output_path=Path(tmp) / "empty_durability.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                max_rounds=1,
                recovery_mode="none",
            )

        self.assertLessEqual(result["by_scenario"]["DISK-001"]["breakdown"]["permanent_fix"], 0.25)

    def test_last_valid_json_object_is_selected(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            final = (
                '{"status":"incident","detected_problem":{"type":"resource.disk","subtype":"tmp_dir_full",'
                '"confidence":1,"evidence":["metric:disk_pct","log:ENOSPC"]},'
                '"root_cause":{"label":"temp_cache_no_retention","confidence":1,"evidence":["log:ENOSPC"]},'
                '"actions":[],"expected_outcome":"Diagnose.","risk":"medium","human_message":"Disk incident."}'
            )
            raw = f'analysis draft {{"status":"ok"}} final {final}'
            return raw, {"prompt_tokens": 10, "completion_tokens": 20}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "last_json.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                max_rounds=1,
                recovery_mode="none",
            )

        record = next(r for r in result["records"] if r["scenario_id"] == "DISK-001")
        self.assertEqual(record["decision"]["status"], "incident")
        self.assertEqual(result["efficiency"]["malformed_output_rate"], 0.0)

    def test_nested_valid_object_inside_malformed_outer_object_is_rejected(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            inner = (
                '{"status":"incident","detected_problem":{"type":"resource.disk","subtype":"tmp_dir_full",'
                '"confidence":1,"evidence":["metric:disk_pct"]},"root_cause":{"label":"temp_cache_no_retention",'
                '"confidence":1,"evidence":["log:ENOSPC"]},"actions":[],"expected_outcome":"Diagnose.",'
                '"risk":"medium","human_message":"Disk incident."}'
            )
            raw = f'prefix {{"outer": invalid {inner}}} suffix'
            return raw, {"prompt_tokens": 10, "completion_tokens": 20}, {
                "finish_reason": "stop",
                "content": raw,
                "reasoning_content": "",
            }

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=Path(tmp) / "nested_json.json",
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="strict_json",
                max_rounds=1,
                recovery_mode="none",
            )

        self.assertGreater(result["efficiency"]["malformed_output_rate"], 0)
        self.assertEqual(result["records"][0]["decision"]["status"], "need_more_info")

    def test_llama_trajectories_are_preserved_and_inspectable(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str, grammar: str | None = None):
            raw = '{"s":0,"t":0,"u":0,"r":0,"a":[]}'
            return (
                raw,
                {"prompt_tokens": 10, "completion_tokens": 10},
                {
                    "finish_reason": "stop",
                    "content": "",
                    "reasoning_content": raw,
                    "raw_api_response": {"choices": [{"message": {"reasoning_content": raw}}]},
                    "request_body": {"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                },
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            report_path = Path(tmp) / "trace_report.json"
            trace_dir = Path(tmp) / "traces"
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "disk",
                output_path=report_path,
                agent_mode="llama_json",
                base_url="http://unused.invalid/v1",
                model="fake-model",
                prompt_style="micro_json",
                harness_profile="tinyagent_style",
                tool_mode="retrieval",
                memory_mode="none",
                max_rounds=1,
                recovery_mode="none",
                grammar_mode="micro_json",
                trace_dir=trace_dir,
            )
            artifact_path = Path(result["trace_archive"]["artifacts"][0])
            artifact = json.loads(artifact_path.read_text())
            analysis = inspect_benchmark_report(report_path=report_path, scenarios_dir=ROOT / "scenarios" / "disk")

            self.assertTrue(artifact_path.exists())
            self.assertTrue(artifact["trajectory_integrity"]["has_system_prompt"])
            self.assertTrue(artifact["trajectory_integrity"]["has_user_prompt"])
            self.assertTrue(artifact["trajectory_integrity"]["has_raw_reasoning_content"])
            self.assertEqual(analysis["trace_checks"]["records_with_artifact"], result["trace_archive"]["num_artifacts"])
            self.assertGreaterEqual(len(analysis["prompt_improvement_lines"]), 1)


if __name__ == "__main__":
    unittest.main()
