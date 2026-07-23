from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import threading
import unittest
import tempfile
from unittest.mock import patch

from harness.contracts import load_benchmark_contract, validate_telemetry
from harness.event_feed import WorldState
from harness.maintenance_loop import (
    BashResult,
    MaintenanceLoop,
    ToolCall,
    WakeupResult,
    OpenAIModelTransport,
    truncate_conversation,
)
from harness.maintenance_daemon import EscalationStore
from harness.model_under_test import (
    ModelTarget,
    create_model_under_test,
    project_visible_output,
)
from harness.target_resolution import resolve_target
from harness.tool_registry import ToolRegistry
from harness.telemetry_archive import TelemetryArchive
from harness.telemetry_source import PeriodicTelemetrySource
from harness.baseline_agent import BaselineRuleAgent
from harness.scenario_schema import load_scenarios


ROOT = Path(__file__).resolve().parents[1]


class HarnessArchitectureTests(unittest.TestCase):
    def test_maintenance_contract_is_external_and_minimal(self) -> None:
        contract = load_benchmark_contract(ROOT / "benchmarks" / "maintenance_v1")

        self.assertIn(
            "strictly better to preserve state and escalate",
            contract.system_prompt.lower(),
        )
        self.assertIn(
            "must be passed directly",
            contract.bash_tool["function"]["description"].lower(),
        )
        self.assertFalse(
            (
                ROOT
                / "benchmarks"
                / "maintenance_v1"
                / "schemas"
                / "final.schema.json"
            ).exists()
        )
        validate_telemetry(
            json.loads(
                (
                    ROOT
                    / "benchmarks"
                    / "maintenance_v1"
                    / "examples"
                    / "wakeup.json"
                ).read_text(encoding="utf-8")
            )
        )
        self.assertEqual(contract.bash_tool["function"]["name"], "bash")
        self.assertEqual(
            set(contract.bash_tool["function"]["parameters"]["properties"]),
            {"command"},
        )
        self.assertNotIn("final_schema", contract.manifest)

    def test_model_facing_prompt_prose_is_not_embedded_in_agent_module(self) -> None:
        source = (ROOT / "harness" / "llm_agent.py").read_text(encoding="utf-8")

        self.assertNotIn("You are an edge auto-maintenance agent", source)
        self.assertNotIn("This is a monitoring wake-up tick", source)
        self.assertNotIn("You are a senior SRE", source)

    def test_wakeup_signal_is_host_wide_and_has_no_scheduler_metadata(self) -> None:
        telemetry = json.loads(
            (
                ROOT
                / "benchmarks"
                / "maintenance_v1"
                / "examples"
                / "wakeup.json"
            ).read_text(encoding="utf-8")
        )

        self.assertNotIn("round", telemetry)
        self.assertNotIn("elapsed_s", telemetry)
        self.assertNotIn("trigger", telemetry)
        self.assertNotIn("schema_version", telemetry)
        self.assertNotIn("host", telemetry)
        self.assertNotIn("collector", telemetry)
        self.assertEqual(telemetry["escalating"], [])
        self.assertEqual(
            [item["name"] for item in telemetry["network_interfaces"]],
            ["eth0"],
        )
        self.assertEqual(
            telemetry["notable_processes"][0]["state"],
            "zombie",
        )
        api = next(item for item in telemetry["services"] if item["name"] == "api.service")
        self.assertEqual(api["stderr"]["new_line_count"], 37)
        self.assertEqual(len(api["stderr"]["lines"]), 2)
        self.assertEqual(api["events"][0]["code"], "health_check_timeout")

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

            files = sorted(
                path
                for path in Path(tmp).glob("*.json")
                if path.name != "latest.json"
            )
            self.assertEqual(
                [path.name for path in files],
                [
                    "20260722T063100.000000Z.json",
                    third.name,
                ],
            )
            self.assertFalse(first.exists())
            self.assertEqual(
                (Path(tmp) / "latest.json").resolve(),
                third.resolve(),
            )

    def test_periodic_telemetry_keeps_collecting_and_returns_latest_snapshot(self) -> None:
        collected_three = threading.Event()
        calls = 0

        def collect() -> dict[str, int]:
            nonlocal calls
            calls += 1
            if calls >= 3:
                collected_three.set()
            return {"sequence": calls}

        with PeriodicTelemetrySource(collect, interval_s=0.01) as source:
            first = source.next()
            self.assertTrue(collected_three.wait(timeout=1))
            latest = source.next()

        self.assertEqual(first, {"sequence": 1})
        self.assertGreaterEqual(latest["sequence"], 3)

    def test_fresh_model_loop_retries_missing_tool_call_then_finishes_ok(self) -> None:
        class FakeTransport:
            def __init__(self) -> None:
                self.requests: list[list[dict]] = []

            def complete(self, *, messages, tools, tool_choice):
                self.requests.append(json.loads(json.dumps(messages)))
                if len(self.requests) == 1:
                    return {"content": "Everything appears healthy.", "tool_calls": []}
                return {
                    "content": "",
                    "tool_calls": [
                        ToolCall(
                            id="call-1",
                            name="bash",
                            arguments={"command": "everything_ok"},
                        )
                    ],
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text(
                "# Demo host\n\nRestart api.service after changing its configuration.\n",
                encoding="utf-8",
            )
            memory = root / "MEMORY.md"
            memory.write_text("Known service: api.service\n", encoding="utf-8")
            archive = TelemetryArchive(root / "telemetry", max_files=10, max_age_s=None)
            transport = FakeTransport()
            loop = MaintenanceLoop(
                transport=transport,
                command_executor=lambda command: BashResult(0, "", ""),
                system_prompt="Maintain the host safely.",
                bash_tool={"type": "function", "function": {"name": "bash", "parameters": {}}},
                project_readme_path=readme,
                memory_path=memory,
                telemetry_archive=archive,
                max_steps=4,
                max_context_tokens=4096,
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(
            transport.requests[0][0],
            {"role": "system", "content": "Maintain the host safely."},
        )
        self.assertEqual(transport.requests[0][1]["role"], "user")
        first_user = transport.requests[0][1]["content"]
        self.assertLess(first_user.index("# Project README"), first_user.index("# Memory"))
        self.assertLess(first_user.index("# Memory"), first_user.index("# Current telemetry"))
        self.assertIn("Restart api.service", first_user)
        self.assertIn("Known service: api.service", first_user)
        self.assertIn('"observed_at": "2026-07-22T06:30:00Z"', first_user)
        self.assertEqual(
            transport.requests[1][-2],
            {"role": "assistant", "content": "Everything appears healthy."},
        )
        self.assertIn("Call bash exactly once", transport.requests[1][-1]["content"])

    def test_bash_loop_executes_command_then_escalates_with_stable_reason(self) -> None:
        class FakeTransport:
            def __init__(self) -> None:
                self.index = 0

            def complete(self, *, messages, tools, tool_choice):
                commands = [
                    "jq '.services[] | .name' telemetry/latest.json",
                    "escalate temporary repair_restores_service_but_does_not_persist",
                ]
                command = commands[self.index]
                self.index += 1
                return {
                    "content": "",
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.index}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ],
                }

        executed: list[str] = []

        def execute(command: str) -> BashResult:
            executed.append(command)
            return BashResult(0, "api.service\n", "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            memory = root / "MEMORY.md"
            archive = TelemetryArchive(root / "telemetry", max_files=10, max_age_s=None)
            loop = MaintenanceLoop(
                transport=FakeTransport(),
                command_executor=execute,
                system_prompt="Maintain the host.",
                bash_tool={"type": "function", "function": {"name": "bash", "parameters": {}}},
                project_readme_path=readme,
                memory_path=memory,
                telemetry_archive=archive,
                max_steps=4,
                max_context_tokens=4096,
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(executed, ["jq '.services[] | .name' telemetry/latest.json"])
        self.assertEqual(result.terminal, "escalate")
        self.assertEqual(result.escalation_level, "temporary")
        self.assertEqual(
            result.message,
            "repair_restores_service_but_does_not_persist",
        )

    def test_wrapped_terminal_control_is_rejected_without_execution(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = ['echo "everything_ok"', "everything_ok"]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(executed, [])
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "bare control value" in str(message.get("content", ""))
                for message in result.messages
            )
        )

    def test_context_document_reread_is_rejected_without_execution(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = ["cat /sandbox/MEMORY.md", "everything_ok"]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            memory = root / "MEMORY.md"
            memory.write_text("memory", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=memory,
                telemetry_archive=TelemetryArchive(root / "telemetry"),
                memory_display_path="/sandbox/MEMORY.md",
                project_readme_display_path="/sandbox/README.md",
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(executed, [])
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "Do not reread MEMORY.md with bash." in str(message.get("content", ""))
                for message in result.messages
            )
        )

    def test_persistent_mutation_requires_same_cycle_backup(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = [
                    "sed -i 's/^KEY=.*/KEY=2/' /sandbox/etc/demo-api/worker.env",
                    "cp --preserve=all -- /sandbox/etc/demo-api/worker.env /sandbox/etc/demo-api/worker.env.maint-backup",
                    "sed -i 's/^KEY=.*/KEY=2/' /sandbox/etc/demo-api/worker.env",
                    "everything_ok",
                ]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(
            executed,
            [
                "cp --preserve=all -- /sandbox/etc/demo-api/worker.env /sandbox/etc/demo-api/worker.env.maint-backup",
                "sed -i 's/^KEY=.*/KEY=2/' /sandbox/etc/demo-api/worker.env",
            ],
        )
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "Before editing a persistent file under /sandbox/etc/" in str(
                    message.get("content", "")
                )
                for message in result.messages
            )
        )

    def test_host_paths_outside_sandbox_are_rejected(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = ["cat /var/run/demo.pid", "everything_ok"]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(executed, [])
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "permits file operations only under `/sandbox/...`" in str(
                    message.get("content", "")
                )
                for message in result.messages
            )
        )

    def test_cd_sandbox_relative_workflow_is_rejected(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = ["cd /sandbox && cat etc/demo-api/config.yaml", "everything_ok"]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(executed, [])
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "Do not `cd /sandbox`" in str(message.get("content", ""))
                for message in result.messages
            )
        )

    def test_temp_cache_file_backup_copy_is_rejected(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = [
                    "cp --preserve=all -- /sandbox/var/tmp/demo-cache/a.bin /sandbox/var/tmp/demo-cache/a.bin.maint-backup",
                    "everything_ok",
                ]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(executed, [])
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "Do not copy temporary cache files to `.maint-backup`" in str(
                    message.get("content", "")
                )
                for message in result.messages
            )
        )

    def test_restore_is_rejected_without_failed_verification(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = [
                    "cp --preserve=all -- /sandbox/etc/demo-api/worker.env /sandbox/etc/demo-api/worker.env.maint-backup",
                    "cp --preserve=all -- /sandbox/etc/demo-api/worker.env.maint-backup /sandbox/etc/demo-api/worker.env",
                    "escalate failed needs_human",
                ]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "escalate")
        self.assertEqual(executed, ["cp --preserve=all -- /sandbox/etc/demo-api/worker.env /sandbox/etc/demo-api/worker.env.maint-backup"])
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "Restore from `.maint-backup` only after a failed verification" in str(
                    message.get("content", "")
                )
                for message in result.messages
            )
        )

    def test_evidence_artifact_overwrite_is_rejected(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = [
                    "find /sandbox/var/tmp/demo-cache -type f | sort > /sandbox/var/tmp/demo-cache.maint-backup-list",
                    "find /sandbox/var/tmp/demo-cache -type f | sort > /sandbox/var/tmp/demo-cache.maint-backup-list && echo second",
                    "everything_ok",
                ]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(
            executed,
            ["find /sandbox/var/tmp/demo-cache -type f | sort > /sandbox/var/tmp/demo-cache.maint-backup-list"],
        )
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "would overwrite an existing maintenance evidence artifact" in str(
                    message.get("content", "")
                )
                for message in result.messages
            )
        )

    def test_repeated_readonly_successes_trigger_terminal_guidance(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = [
                    "cat /sandbox/etc/demo-api/worker.env",
                    "systemctl status demo-api",
                    "ls -la /sandbox/etc/demo-api",
                    "grep WORKER /sandbox/etc/demo-api/worker.env",
                    "everything_ok",
                ]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda _: BashResult(0, "", ""),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "repeated successful read-only verification evidence" in str(
                    message.get("content", "")
                )
                for message in result.messages
            )
        )

    def test_terminal_is_required_after_readonly_guidance(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = [
                    "cat /sandbox/etc/demo-api/worker.env",
                    "systemctl status demo-api",
                    "ls -la /sandbox/etc/demo-api",
                    "grep WORKER /sandbox/etc/demo-api/worker.env",
                    "cat /sandbox/etc/demo-api/worker.env",
                    "everything_ok",
                ]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(
            executed,
            [
                "cat /sandbox/etc/demo-api/worker.env",
                "systemctl status demo-api",
                "ls -la /sandbox/etc/demo-api",
                "grep WORKER /sandbox/etc/demo-api/worker.env",
            ],
        )
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "Your next bash call must be exactly `everything_ok`" in str(
                    message.get("content", "")
                )
                for message in result.messages
            )
        )

    def test_everything_ok_rejected_when_actionable_telemetry_has_no_work(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = [
                    "everything_ok",
                    "cp --preserve=all -- /sandbox/etc/demo-api/config.yaml /sandbox/etc/demo-api/config.yaml.maint-backup",
                    "everything_ok",
                ]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        telemetry = {
            "observed_at": "2026-07-22T06:30:00Z",
            "services": [
                {
                    "name": "demo-api",
                    "state": "failed",
                    "health": "unhealthy",
                    "events": [{"severity": "error", "message": "failed"}],
                }
            ],
            "host_events": [],
            "notable_processes": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            executed: list[str] = []
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: (
                    executed.append(command) or BashResult(0, "", "")
                ),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup(telemetry)

        self.assertEqual(result.terminal, "everything_ok")
        self.assertEqual(
            executed,
            ["cp --preserve=all -- /sandbox/etc/demo-api/config.yaml /sandbox/etc/demo-api/config.yaml.maint-backup"],
        )
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "Do not call everything_ok yet." in str(message.get("content", ""))
                for message in result.messages
            )
        )

    def test_bash_loop_preserves_assistant_reasoning_between_tool_calls(self) -> None:
        testcase = self

        class StatefulTransport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, *, messages, tools, tool_choice):
                del tools, tool_choice
                self.calls += 1
                if self.calls == 1:
                    return {
                        "content": "I will inspect the current value.",
                        "reasoning_content": "Inspect first, then edit the confirmed bad value.",
                        "tool_calls": [
                            ToolCall(
                                id="call-1",
                                name="bash",
                                arguments={"command": "cat /sandbox/etc/demo.env"},
                            )
                        ],
                    }
                previous = messages[-2]
                testcase.assertEqual(previous["role"], "assistant")
                testcase.assertEqual(
                    previous["content"],
                    "I will inspect the current value.",
                )
                testcase.assertEqual(
                    previous["reasoning_content"],
                    "Inspect first, then edit the confirmed bad value.",
                )
                return {
                    "content": "",
                    "reasoning_content": "Inspection is complete.",
                    "tool_calls": [
                        ToolCall(
                            id="call-2",
                            name="bash",
                            arguments={"command": "everything_ok"},
                        )
                    ],
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            loop = MaintenanceLoop(
                transport=StatefulTransport(),
                command_executor=lambda _: BashResult(0, "VALUE=bad\n", ""),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "everything_ok")

    def test_context_truncation_never_removes_system_prompt(self) -> None:
        messages = [
            {"role": "system", "content": "permanent instructions"},
            {"role": "user", "content": "x" * 400},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"id": "one"}],
            },
            {"role": "tool", "tool_call_id": "one", "content": "y" * 400},
            {"role": "user", "content": "latest reminder"},
        ]

        truncated = truncate_conversation(
            messages,
            max_context_tokens=100,
            target_fraction=0.5,
        )

        self.assertEqual(truncated[0], messages[0])
        self.assertLess(len(truncated), len(messages))

    def test_wakeup_audit_preserves_turns_removed_from_model_context(self) -> None:
        class Transport:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, **_: object) -> dict[str, object]:
                commands = ["echo one", "echo two", "echo three", "everything_ok"]
                command = commands[self.calls]
                self.calls += 1
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            loop = MaintenanceLoop(
                transport=Transport(),
                command_executor=lambda command: BashResult(0, command, ""),
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
                max_context_tokens=80,
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        audited_commands = [
            json.loads(message["tool_calls"][0]["function"]["arguments"])["command"]
            for message in result.messages
            if message.get("role") == "assistant" and message.get("tool_calls")
        ]
        self.assertEqual(
            audited_commands,
            ["echo one", "echo two", "echo three", "everything_ok"],
        )

    def test_repeated_identical_bash_result_gets_no_progress_reminder(self) -> None:
        class RepeatingTransport:
            def __init__(self) -> None:
                self.seen_messages: list[list[dict[str, object]]] = []
                self.calls = 0

            def complete(self, **kwargs: object) -> dict[str, object]:
                messages = kwargs["messages"]
                assert isinstance(messages, list)
                self.seen_messages.append(messages)
                self.calls += 1
                command = "ls /missing" if self.calls <= 2 else "escalate unlocated path is absent"
                return {
                    "tool_calls": [
                        ToolCall(
                            id=f"call-{self.calls}",
                            name="bash",
                            arguments={"command": command},
                        )
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Test host\n", encoding="utf-8")
            transport = RepeatingTransport()
            executed: list[str] = []

            def execute(command: str) -> BashResult:
                executed.append(command)
                return BashResult(2, "", "not found")

            loop = MaintenanceLoop(
                transport=transport,
                command_executor=execute,
                system_prompt="Maintain the host.",
                bash_tool={"type": "function"},
                project_readme_path=readme,
                memory_path=root / "MEMORY.md",
                telemetry_archive=TelemetryArchive(root / "telemetry"),
            )
            result = loop.run_wakeup({"observed_at": "2026-07-22T06:30:00Z"})

        self.assertEqual(result.terminal, "escalate")
        self.assertEqual(executed, ["ls /missing"])
        self.assertTrue(
            any(
                message.get("role") == "user"
                and "was not executed" in str(message.get("content", "")).lower()
                for message in transport.seen_messages[-1]
            )
        )

    def test_model_transport_uses_native_tool_call_without_output_schema(self) -> None:
        captured: dict[str, object] = {}

        class Response:
            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *_: object) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps(
                    {
                        "choices": [
                            {
                                "finish_reason": "tool_calls",
                                "message": {
                                    "tool_calls": [
                                        {
                                            "id": "call-1",
                                            "type": "function",
                                            "function": {
                                                "name": "bash",
                                                "arguments": "{\"command\":\"everything_ok\"}",
                                            },
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ).encode()

        def fake_urlopen(req: object, timeout: float) -> Response:
            del timeout
            captured.update(json.loads(req.data.decode("utf-8")))
            return Response()

        transport = OpenAIModelTransport(
            base_url="http://127.0.0.1:8080/v1",
            model="tiny-model",
        )
        with patch("harness.maintenance_loop.request.urlopen", fake_urlopen):
            result = transport.complete(
                messages=[{"role": "user", "content": "{}"}],
                tools=[{"type": "function", "function": {"name": "bash"}}],
                tool_choice="required",
            )

        self.assertEqual(captured["tool_choice"], "required")
        self.assertEqual(captured["temperature"], 0.2)
        self.assertEqual(captured["top_p"], 0.9)
        self.assertEqual(captured["top_k"], 40)
        self.assertEqual(captured["min_p"], 0.05)
        self.assertEqual(captured["presence_penalty"], 0.05)
        self.assertEqual(captured["frequency_penalty"], 0.05)
        self.assertEqual(captured["seed"], 42)
        self.assertEqual(captured["repeat_penalty"], 1.05)
        self.assertEqual(captured["repeat_last_n"], 256)
        self.assertEqual(captured["tools"], [{"type": "function", "function": {"name": "bash"}}])
        self.assertNotIn("response_format", captured)
        self.assertNotIn("grammar", captured)
        self.assertNotIn("json_schema", captured)
        self.assertEqual(result["finish_reason"], "tool_calls")
        self.assertEqual(result["tool_calls"][0].name, "bash")

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

            self.assertEqual(
                telemetry["escalating"][0]["id"],
                "esc_0123456789ab",
            )
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

    def test_visible_output_projection_excludes_reasoning_and_uses_last_output(self) -> None:
        projection = project_visible_output(
            [
                {"type": "assistant.message", "content": "intermediate"},
                {"type": "assistant.reasoning", "content": "hidden chain of thought"},
                {"type": "tool.result", "content": "file contents"},
                {"type": "assistant.message", "content": '{"response":"none"}'},
            ]
        )

        self.assertEqual(
            [message.content for message in projection.visible_outputs],
            ["intermediate", '{"response":"none"}'],
        )
        self.assertEqual(projection.final_output, '{"response":"none"}')
        self.assertNotIn("hidden chain of thought", projection.final_output)

    def test_model_factory_hides_legacy_target_selection(self) -> None:
        target = create_model_under_test(ModelTarget(kind="baseline"))

        self.assertIsInstance(target, BaselineRuleAgent)

    def test_target_resolution_supports_only_direct_models(self) -> None:
        raw = resolve_target(model="./model.gguf", base_url=None)
        named = resolve_target(
            model="qwen",
            base_url="http://127.0.0.1:8080/v1",
        )

        self.assertTrue(raw.local_model)
        self.assertEqual(raw.kind, "raw")
        self.assertFalse(named.local_model)
        with self.assertRaisesRegex(ValueError, "requires --base-url"):
            resolve_target(model="qwen", base_url=None)

    def test_tool_registry_builds_disjoint_union_and_dispatches(self) -> None:
        registry = ToolRegistry(ROOT / "plugins" / "tools")
        schema = registry.union_schema(["inspect_metrics", "cleanup_tmp"])
        discriminators = {
            item["properties"]["type"]["const"]
            for item in schema["oneOf"]
        }
        state = WorldState.from_baseline({"metrics": {"cpu_pct": 42}})
        scenario = load_scenarios(ROOT / "scenarios" / "cpu")[0]

        result = registry.invoke(
            {"type": "inspect_metrics", "args": {}},
            state=state,
            scenario=scenario,
        )

        self.assertEqual(discriminators, {"inspect_metrics", "cleanup_tmp"})
        self.assertTrue(result.ok)
        self.assertEqual(result.observation["metrics"]["cpu_pct"], 42)
        with self.assertRaisesRegex(ValueError, "unknown tool"):
            registry.invoke(
                {"type": "not_registered", "args": {}},
                state=state,
                scenario=scenario,
            )
        with self.assertRaisesRegex(ValueError, "invalid tool call"):
            registry.invoke(
                {"type": "adjust_fd_limit", "args": {"limit": "many"}},
                state=state,
                scenario=scenario,
            )
        self.assertNotIn("fd_limit", state.signals)


if __name__ == "__main__":
    unittest.main()
