from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from harness.contracts import load_harness_contract, validate_telemetry
from harness.maintenance_daemon import EscalationStore
from harness.maintenance_loop import WakeupResult
from harness.rejections import load_rejection_rules, match_rejection
from harness.telemetry_archive import TelemetryArchive


ROOT = Path(__file__).resolve().parents[1]


class HarnessArchitectureTests(unittest.TestCase):
    def test_maintenance_contract_is_external_and_minimal(self) -> None:
        contract = load_harness_contract(ROOT / "harness")

        self.assertIn("escalate", contract.system_prompt.lower())
        self.assertEqual(contract.bash_tool["function"]["name"], "bash")
        self.assertEqual(
            set(contract.bash_tool["function"]["parameters"]["properties"]),
            {"command"},
        )
        self.assertEqual(contract.bash_tool["type"], "function")

    def test_model_prompt_is_owned_by_harness_layer(self) -> None:
        prompt = (ROOT / "harness" / "PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("bash only", prompt.lower())
        self.assertIn("everything_ok", prompt)
        self.assertIn("escalate", prompt)

    def test_wakeup_validator_rejects_missing_required_fields(self) -> None:
        telemetry = json.loads(
            (
                ROOT
                / "benchmarks"
                / "maintenance_v1"
                / "examples"
                / "wakeup.json"
            ).read_text(encoding="utf-8")
        )
        del telemetry["services"]
        with self.assertRaisesRegex(ValueError, "telemetry.services"):
            validate_telemetry(telemetry)

    def test_telemetry_trend_current_sample_must_match_current_value(self) -> None:
        telemetry = json.loads(
            (
                ROOT
                / "benchmarks"
                / "maintenance_v1"
                / "examples"
                / "wakeup.json"
            ).read_text(encoding="utf-8")
        )
        contradictory = deepcopy(telemetry)
        contradictory["cpu"]["usage_pct_trend"][telemetry["observed_at"]] = 12
        with self.assertRaisesRegex(ValueError, "cpu.usage_pct_trend"):
            validate_telemetry(contradictory)

    def test_rejection_rules_are_loaded_from_rejections_dir(self) -> None:
        rules = load_rejection_rules(ROOT / "harness" / "rejections")
        self.assertGreaterEqual(len(rules), 1)

        sudo = match_rejection("sudo systemctl status demo-api", rules)
        self.assertIsNotNone(sudo)
        self.assertIn("sudo", sudo.name)

    def test_escalations_are_injected_and_cleared_by_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EscalationStore(Path(tmp) / "escalations.json")
            raised = WakeupResult(
                terminal="escalate",
                message="durable repair requires vendor package",
                escalation_level="blocked",
                escalation_id="esc_0123456789ab",
                messages=(),
                telemetry_path=Path(tmp) / "telemetry.json",
            )
            store.apply(raised, now="2026-07-22T06:30:00Z")
            telemetry = store.inject({"services": []})
            self.assertEqual(telemetry["escalating"][0]["id"], "esc_0123456789ab")

            cleared = WakeupResult(
                terminal="escalate_none",
                message="esc_0123456789ab",
                escalation_level="none",
                escalation_id=None,
                messages=(),
                telemetry_path=Path(tmp) / "telemetry.json",
            )
            store.apply(cleared, now="2026-07-22T06:31:00Z")
            self.assertEqual(store.inject({"services": []})["escalating"], [])

    def test_telemetry_archive_writes_timestamped_json_and_rotates(self) -> None:
        payload = json.loads(
            (
                ROOT
                / "benchmarks"
                / "maintenance_v1"
                / "examples"
                / "wakeup.json"
            ).read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as tmp:
            archive = TelemetryArchive(Path(tmp), max_files=2, max_age_s=None)
            first = archive.store(payload, observed_at="2026-07-22T06:30:00Z")
            archive.store(payload, observed_at="2026-07-22T06:31:00Z")
            third = archive.store(payload, observed_at="2026-07-22T06:32:00Z")

            self.assertTrue(first.exists() is False)
            self.assertTrue(third.exists())
            self.assertTrue((Path(tmp) / "latest.json").is_symlink())


if __name__ == "__main__":
    unittest.main()
