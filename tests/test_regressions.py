from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from harness.framework_adapters import get_adapter
from harness.runner import run_benchmark
from harness.llm_agent import LlamaJSONAgent


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkRegressionTests(unittest.TestCase):
    def test_baseline_examples_are_high_scoring_and_use_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "examples",
                output_path=Path(tmp) / "baseline.json",
                agent_mode="baseline_rule",
            )
        self.assertGreaterEqual(result["summary"]["overall_score"], 85)
        self.assertGreater(result["efficiency"]["mean_tool_calls"], 0)

    def test_llama_empty_content_recovery_executes_fix_tools(self) -> None:
        def fake_chat(self: LlamaJSONAgent, *, system: str, user: str):
            return (
                "The disk is full and ENOSPC appears, so cleanup is needed.",
                {"prompt_tokens": 10, "completion_tokens": 12},
                {"finish_reason": "length", "content": "", "reasoning_content": "The disk is full and ENOSPC appears."},
            )

        with tempfile.TemporaryDirectory() as tmp, patch.object(LlamaJSONAgent, "_chat", fake_chat):
            result = run_benchmark(
                scenarios_dir=ROOT / "scenarios" / "examples",
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

        disk = result["by_scenario"]["resource.disk.tmp_full.quick.v1"]
        self.assertGreaterEqual(disk["score"], 80)
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


if __name__ == "__main__":
    unittest.main()
