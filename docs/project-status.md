# Auto Maintain Bench project status

## Classification

**Research prototype (closed milestone).** The repository provides a deterministic, observable benchmark for tiny language models performing bounded Linux maintenance tasks. It was never a production auto-remediation service.

## Status

Closed as a milestone (2026-09-29). The corpus and harness reached a usable
research state; no active development is planned. Future work may continue in
[Help Agent](https://github.com/ZisIsNotZis/helpagent), which may supersede this
benchmark.

## Evidence

- The corpus currently contains 184 scenario definitions in 19 categories.
- The harness scores fix, durability, safety, and terminal behavior without an
  LLM judge.
- The standard-library tests cover harness behavior and architecture; Docker
  runs are environment-dependent.
- `BENCHMARKS.md` and `docs/FAIL_PATTERNS.md` record dated experiments and
  limitations.

## Version and reproducibility

The benchmark uses version labels such as `v12` for optimization passes rather than a packaged release version. Record model, prompt, temperature, concurrency, Docker image, host resources, and commit with each comparable run. The canonical run command and current methodology are in `CLAUDE.md` and `README.md`.

## Deferred

A complete paper package, approved video artifact, and stable packaged release
(version labels such as `v12` are optimization passes, not releases) were left
undone.
