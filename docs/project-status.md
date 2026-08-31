# Auto Maintain Bench project status

## Classification

**Innovative, research prototype.** The repository provides a deterministic,
observable benchmark for tiny language models performing bounded Linux
maintenance tasks. It is not a production auto-remediation service.

## Evidence

- The corpus currently contains 184 scenario definitions in 19 categories.
- The harness scores fix, durability, safety, and terminal behavior without an
  LLM judge.
- The standard-library tests cover harness behavior and architecture; Docker
  runs are environment-dependent.
- `BENCHMARKS.md` and `docs/FAIL_PATTERNS.md` record dated experiments and
  limitations.

## Version and reproducibility

The benchmark uses version labels such as `v12` for optimization passes rather
than a packaged release version. Record model, prompt, temperature, concurrency,
Docker image, host resources, and commit with each comparable run. The canonical
run command and current methodology are in `CLAUDE.md` and `README.md`.

## Paper and media

The repository has research notes but no complete paper package or approved
video artifact. A paper outline, evidence map, screenshot, or video plan should
be prepared manually once claims and baselines are stable; nothing is uploaded
to arXiv or Bilibili by this repository update.
