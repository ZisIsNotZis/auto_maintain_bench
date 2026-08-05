#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import statistics
import threading
import time

from harness.bash_sandbox_benchmark import (
    BashScenario,
    BashScenarioHarness,
    DockerSandbox,
    load_bash_scenarios,
)
from harness.contracts import load_harness_contract
from harness.local_llama import local_llama_server
from harness.maintenance_loop import ModelTransport, OpenAIModelTransport


ROOT = Path(__file__).resolve().parent

_print_lock = threading.Lock()


def _parse_model_path(model: str) -> tuple[str, str]:
    """Parse model path into (model_name, quant).

    Local GGUF: 'Qwen3.5-2B-UD-Q4_K_XL.gguf' → ('Qwen3.5-2B-UD', 'Q4_K_XL')
    Remote: 'Qwen3.5-2B-UD' → ('Qwen3.5-2B-UD', 'unknown')
    """
    # Strip .gguf extension if present (for local file paths)
    stem = model[:-5] if model.endswith(".gguf") else model
    parts = stem.split("-")
    if len(parts) >= 2 and ("K_" in parts[-1] or "I" in parts[-1] or "IQ" in parts[-1]):
        # Looks like a quant suffix
        quant = parts[-1]
        model_name = "-".join(parts[:-1])
    else:
        model_name = stem
        quant = "unknown"
    return model_name, quant


def _trajectory_path(
    *,
    trajectory_dir: Path,
    model_name: str,
    quant: str,
    version: str,
    scenario_id: str,
    temperature: float,
) -> Path:
    """Build the trajectory path: <dir>/<model_name>/<quant>/<version>/<sid>/t<temp>.json."""
    temp_str = f"t{temperature}".replace(".", "_")
    return (
        trajectory_dir
        / model_name
        / quant
        / version
        / str(scenario_id)
        / f"{temp_str}.json"
    )


def _is_completed(*, scenario_id: str, force: bool, **kwargs: object) -> bool:
    """True if a trajectory already exists for this scenario and force is off."""
    if force:
        return False
    return _trajectory_path(scenario_id=scenario_id, **kwargs).exists()


def _save_trajectory(
    row: dict[str, object],
    *,
    trajectory_dir: Path,
    model_name: str,
    quant: str,
    version: str,
    temperature: float,
    force: bool,
) -> None:
    """Save a scenario trajectory to disk. Skip if already exists unless force."""
    sid = str(row["scenario_id"])
    traj_path = _trajectory_path(
        trajectory_dir=trajectory_dir,
        model_name=model_name,
        quant=quant,
        version=version,
        scenario_id=sid,
        temperature=temperature,
    )

    if traj_path.exists() and not force:
        eprint(f"  trajectory exists, skipping: {traj_path}")
        return

    traj_data = {
        "model": model_name,
        "quant": quant,
        "version": version,
        "temperature": temperature,
        "scenario_id": sid,
        "score": row["score"],
        "terminal": row["terminal"],
        "escalation_level": row.get("escalation_level"),
        "hierarchy_level": row["hierarchy_level"],
        "checks": row["checks"],
        "check_output": row["check_output"],
        "test_results": row["test_results"],
        "changed_paths": row["changed_paths"],
        "unexpected_changes": row["unexpected_changes"],
        "messages": row["messages"],
        "elapsed_s": row["elapsed_s"],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    traj_path.parent.mkdir(parents=True, exist_ok=True)
    traj_path.write_text(
        json.dumps(traj_data, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    eprint(f"  trajectory: {traj_path.resolve()}")


def eprint(*args: object, **kwargs: object) -> None:
    """Thread-safe print."""
    with _print_lock:
        print(*args, **kwargs)


def run_scenario(
    scenario: BashScenario,
    harness: BashScenarioHarness,
    transport: ModelTransport,
) -> dict[str, object]:
    """Run a single scenario and return its report row."""
    start = time.monotonic()
    result = harness.run(scenario, transport)
    elapsed = time.monotonic() - start
    row = {
        "scenario_id": result.scenario_id,
        "score": result.score,
        "terminal": result.terminal,
        "escalation_level": result.escalation_level,
        "message": result.message,
        "checks": result.checks,
        "check_output": {
            check_id: asdict(output)
            for check_id, output in result.check_output.items()
        },
        "changed_paths": result.changed_paths,
        "unexpected_changes": result.unexpected_changes,
        "messages": result.messages,
        "test_results": result.test_results,
        "hierarchy_level": result.hierarchy_level,
        "elapsed_s": round(elapsed, 1),
    }
    eprint(
        f"  score={result.score:.4f} terminal={result.terminal} "
        f"hierarchy={result.hierarchy_level} "
        f"checks={sum(result.checks.values())}/{len(result.checks)} "
        f"tests={sum(result.test_results.values())}/{len(result.test_results)} "
        f"unexpected={len(result.unexpected_changes)} "
        f"elapsed={elapsed:.0f}s",
    )
    return row


def _setup_transport(args: argparse.Namespace, base_url: str) -> OpenAIModelTransport:
    return OpenAIModelTransport(
        base_url=str(base_url),
        model=args.model,
        timeout_s=args.timeout_s,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=0.95,
        top_k=20,
        min_p=0.0,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        seed=42,
        repeat_penalty=args.repeat_penalty,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run bash-only maintenance scenarios in isolated containers.",
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url")
    parser.add_argument(
        "--scenarios-dir",
        type=Path,
        default=ROOT.parent / "scenarios",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Scenario ID to run; repeat to select multiple",
    )
    parser.add_argument("--output", type=Path, default=Path("log/bash_pilot.json"))
    parser.add_argument("--trajectory-dir", type=Path, default=None,
                        help="Directory to save per-scenario trajectories "
                             "(default: None, no trajectory saving)")
    parser.add_argument("--version", default="v9",
                        help="Version label for this optimization pass "
                             "(e.g. v8, v9; stored in trajectory metadata)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing trajectory files")
    parser.add_argument("--ctx-size", type=int, default=65536,
                        help="Context size for llama-server (default: 32768)")
    parser.add_argument("--docker-image", default="local-os/default:latest")
    parser.add_argument("--timeout-s", type=float, default=180.0)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Model temperature (0.0=deterministic, higher=more exploration)")
    parser.add_argument("--repeat-penalty", type=float, default=1.05,
                        help="Repeat penalty (1.0=none, higher=less repetition)")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of scenarios to run in parallel (default 1). "
        "Each scenario gets its own sandbox; model server must handle N concurrent requests.",
    )
    args = parser.parse_args()

    local = args.model.startswith("./") or args.model.endswith(".gguf")
    if not local and not args.base_url:
        parser.error("--base-url is required unless --model starts with ./")
    if args.concurrency < 1:
        parser.error("--concurrency must be >= 1")

    contract = load_harness_contract(ROOT / "harness")
    scenarios = load_bash_scenarios(args.scenarios_dir)
    selected = set(args.scenario)
    if selected:
        scenarios = [scenario for scenario in scenarios if scenario.id in selected]
        missing = selected - {scenario.id for scenario in scenarios}
        if missing:
            parser.error(f"unknown scenarios: {', '.join(sorted(missing))}")

    server = (
        local_llama_server(
            model=args.model,
            ctx_size=args.ctx_size,
            startup_timeout_s=min(args.timeout_s, 120.0),
        )
        if local
        else nullcontext(args.base_url)
    )

    rows: list[dict[str, object]] = []
    model_name, quant = _parse_model_path(args.model)
    with server as base_url:
        transport = _setup_transport(args, base_url)

        # Pre-create one harness per worker to avoid sharing state
        harnesses = [
            BashScenarioHarness(
                contract=contract,
                sandbox=DockerSandbox(
                    image=args.docker_image,
                    timeout_s=args.timeout_s,
                ),
            )
            for _ in range(min(args.concurrency, len(scenarios)))
        ]

        total = len(scenarios)
        eprint(f"Running {total} scenarios with concurrency {args.concurrency}...")

        if args.concurrency <= 1:
            # Sequential path — same as before, single harness
            harness = harnesses[0]
            for index, scenario in enumerate(scenarios, start=1):
                eprint(
                    f"[scenario {index}/{total}] "
                    f"{scenario.id} | {scenario.title}",
                )
                if args.trajectory_dir is not None and _is_completed(
                    scenario_id=scenario.id,
                    trajectory_dir=args.trajectory_dir,
                    model_name=model_name,
                    quant=quant,
                    version=args.version,
                    temperature=args.temperature,
                    force=args.force,
                ):
                    eprint(f"  trajectory exists, skipping: {scenario.id}")
                    continue
                row = run_scenario(scenario, harness, transport)
                if args.trajectory_dir is not None:
                    _save_trajectory(row, trajectory_dir=args.trajectory_dir,
                                     model_name=model_name, quant=quant,
                                     version=args.version,
                                     temperature=args.temperature,
                                     force=args.force)
                rows.append(row)
        else:
            # Concurrent path — assign scenarios to worker threads
            completed = 0
            with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                futures = {}
                for index, scenario in enumerate(scenarios):
                    if args.trajectory_dir is not None and _is_completed(
                        scenario_id=scenario.id,
                        trajectory_dir=args.trajectory_dir,
                        model_name=model_name,
                        quant=quant,
                        version=args.version,
                        temperature=args.temperature,
                        force=args.force,
                    ):
                        eprint(
                            f"  trajectory exists, skipping: {scenario.id}",
                        )
                        continue
                    h = harnesses[index % len(harnesses)]
                    future = pool.submit(run_scenario, scenario, h, transport)
                    futures[future] = (index + 1, scenario.id, scenario.title)

                for future in as_completed(futures):
                    index, sid, title = futures[future]
                    exc = future.exception()
                    if exc is not None:
                        eprint(f"[scenario {index}/{total}] {sid} | {title}")
                        eprint(f"  ** FAILED: {exc}")
                        rows.append({
                            "scenario_id": sid,
                            "score": 0.0,
                            "terminal": "error",
                            "escalation_level": "failed",
                            "checks": {},
                            "check_output": {},
                            "changed_paths": [],
                            "unexpected_changes": [],
                            "messages": [],
                            "test_results": {},
                            "hierarchy_level": "noop",
                            "elapsed_s": 0.0,
                            "error": str(exc),
                        })
                    else:
                        row = future.result()
                        if args.trajectory_dir is not None:
                            _save_trajectory(row, trajectory_dir=args.trajectory_dir,
                                             model_name=model_name, quant=quant,
                                             version=args.version,
                                             temperature=args.temperature,
                                             force=args.force)
                        rows.append(row)
                    completed += 1
                    eprint(f"  [{completed}/{total}]")

    report = {
        "model": args.model,
        "summary": {
            "scenario_count": len(rows),
            "concurrency": args.concurrency,
            "overall_score": (
                round(statistics.mean(float(row["score"]) for row in rows), 4)
                if rows
                else 0.0
            ),
        },
        "scenarios": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(f"overall_score={report['summary']['overall_score']}")
    print(f"saved={args.output.resolve()}")


if __name__ == "__main__":
    main()
