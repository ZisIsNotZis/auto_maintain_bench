#!/usr/bin/env python3
"""Scan trajectories/ and regenerate BENCHMARKS.md with summary tables.

Usage:
    python3 scripts/update_benchmarks.py [--trajectory-dir trajectories/]

Scans all trajectory files and produces a markdown summary with per-version,
per-model, and per-category breakdowns.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_trajectories(traj_dir: Path) -> list[dict[str, Any]]:
    """Load all trajectory files from the directory tree."""
    trajectories = []
    for path in traj_dir.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_path"] = str(path.relative_to(traj_dir))
            trajectories.append(data)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  WARN: skipping {path}: {e}")
    return trajectories


def _group_by(trajectories, *keys):
    """Group trajectories by key tuple."""
    groups = defaultdict(list)
    for t in trajectories:
        key = tuple(t.get(k, "unknown") for k in keys)
        groups[key].append(t)
    return dict(groups)


def _fmt_score(scores: list[float]) -> str:
    if not scores:
        return "—"
    mean = sum(scores) / len(scores)
    return f"{mean:.2%}"


def _count_tier(trajectories, tier: str) -> int:
    return sum(1 for t in trajectories if t.get("hierarchy_level") == tier)


def _count_terminal(trajectories, term: str) -> int:
    return sum(1 for t in trajectories if t.get("terminal") == term)


def generate_report(trajectories: list[dict[str, Any]]) -> str:
    lines = []
    lines.append("# Benchmarks")
    lines.append("")
    lines.append("Auto-generated from `trajectories/`. Run `python3 scripts/update_benchmarks.py`")
    lines.append("to regenerate.")
    lines.append("")

    # ── Overall summary by version ──
    by_version = _group_by(trajectories, "version", "model", "quant")
    lines.append("## Overall Results")
    lines.append("")
    lines.append("| Version | Model | Quant | Temp | Scenarios | Score | Noop | Fix | eok |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    # Sort versions: extract numeric part for sorting
    def _sort_key(kv):
        ver, model, quant = kv[0]
        # Extract version number
        vnum = 0
        try:
            vnum = int("".join(c for c in ver if c.isdigit()))
        except ValueError:
            pass
        return (vnum, model, quant)

    for (version, model, quant), trajs in sorted(
        by_version.items(), key=_sort_key, reverse=True
    ):
        scores = [t["score"] for t in trajs if "score" in t]
        temp = trajs[0].get("temperature", "?")
        noop = _count_tier(trajs, "noop")
        fix = _count_tier(trajs, "permanent_fix") + _count_tier(trajs, "perm_fix_escalate")
        eok = _count_terminal(trajs, "everything_ok")
        lines.append(
            f"| {version} | {model} | {quant} | {temp} | {len(trajs)} | "
            f"{_fmt_score(scores)} | {noop} | {fix} | {eok} |"
        )

    # ── Category breakdown per version ──
    lines.append("")
    lines.append("## Category Breakdowns")
    lines.append("")

    for (version, model, quant), trajs in sorted(
        by_version.items(), key=_sort_key, reverse=True
    ):
        lines.append(f"### {version} — {model} {quant}")
        lines.append("")
        cats = _group_by(trajs, "scenario_id")
        # Extract category prefix from scenario_id
        cat_groups = defaultdict(list)
        for sid_tuple, sts in cats.items():
            sid = sid_tuple[0]  # _group_by returns tuple keys
            cat = sid.split("-")[0] if "-" in sid else "OTHER"
            cat_groups[cat].extend(sts)

        lines.append("| Category | Count | Mean | Noop | Fix | eok |")
        lines.append("|---|---|---|---|---|---|")
        for cat in sorted(cat_groups.keys()):
            sts = cat_groups[cat]
            scores = [s["score"] for s in sts if "score" in s]
            noop = _count_tier(sts, "noop")
            fix = _count_tier(sts, "permanent_fix") + _count_tier(sts, "perm_fix_escalate")
            eok = _count_terminal(sts, "everything_ok")
            lines.append(
                f"| {cat} | {len(sts)} | {_fmt_score(scores)} | {noop} | {fix} | {eok} |"
            )
        lines.append("")

    # ── Trajectory index ──
    lines.append("## Trajectory Files")
    lines.append("")
    lines.append("| Path | Model | Quant | Version | Scenario | Score |")
    lines.append("|---|---|---|---|---|---|")
    for t in sorted(trajectories, key=lambda x: x.get("_path", "")):
        path = t.get("_path", "")
        model = t.get("model", "?")
        quant = t.get("quant", "?")
        version = t.get("version", "?")
        sid = t.get("scenario_id", "?")
        score = t.get("score", "?")
        lines.append(f"| {path} | {model} | {quant} | {version} | {sid} | {score} |")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate BENCHMARKS.md from trajectory files."
    )
    parser.add_argument(
        "--trajectory-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "trajectories",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "BENCHMARKS.md",
    )
    args = parser.parse_args()

    if not args.trajectory_dir.exists():
        print(f"No trajectories found at {args.trajectory_dir}")
        return

    print(f"Scanning {args.trajectory_dir}...")
    trajs = _load_trajectories(args.trajectory_dir)
    print(f"Found {len(trajs)} trajectory files")

    report = generate_report(trajs)
    args.output.write_text(report, encoding="utf-8")
    print(f"Written to {args.output.resolve()}")


if __name__ == "__main__":
    main()