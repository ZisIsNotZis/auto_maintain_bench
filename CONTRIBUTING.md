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

## Pull Requests

Please include:

- what changed
- why it improves benchmark fidelity
- expected effect on score interpretation
- sample output report (or diff) if behavior changed

