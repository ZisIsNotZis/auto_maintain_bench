# Contributing

## Scope

This project benchmarks auto-maintenance agents on deterministic, sandboxed scenarios.

Contributions are welcome for:

- new scenarios (with deterministic validators)
- new tool simulators/probes
- new agent adapters
- scoring improvements that stay deterministic
- reporting/visualization improvements

## Development

1. Keep benchmark runs deterministic.
2. Do not require cloud APIs.
3. Do not add host-destructive tests.
4. Keep no-LLM-as-judge as default behavior.

## Checks

Run the standard-library test suite before opening a pull request:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

No package installation is needed. Docker-backed cases run when Docker is
available and skip otherwise, so a clean run without Docker is expected on a
machine that has no daemon. If you change scoring or a scenario, also state which
scenario IDs you re-ran and with which model, prompt version, and concurrency.

## Pull Requests

Please include:

- what changed
- why it improves benchmark fidelity
- expected effect on score interpretation
- sample output report (or diff) if behavior changed

## Issues

- Report one problem per issue and name the scenario IDs involved.
- For a low score, check `docs/FAIL_PATTERNS.md` first; a known failure mode
  should be recorded there rather than opened as a fresh issue.
- Include the commit, model, quantization, prompt version, and run command behind
  any number you quote.
