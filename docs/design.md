# Auto-Maintain Bench Design (Authoritative)

This document is the source of truth for architecture boundaries, runtime behavior, and migration rules.

## 1. Migration discipline (non-negotiable)

1. Always validate a few pilots **one by one** first.
2. Ask for explicit confirmation before broad parallel migration.
3. Delete deprecated files/logic after replacement stabilizes (no comment-out/branch-around leftovers).
4. Create/update todos before major implementation phases.
5. **Current state:** migration execution is paused while docs are aligned.

## 2. Layer boundaries (target architecture)

### 2.1 Benchmark layer

- Contains scenario assets and scoring logic only.
- Must not contain model prompts/instructions.
- Evaluates behavior from observable effects (checks/diffs/validators/terminals).

### 2.2 Agent layer

- Owns the runtime policy prompt (`PROMPT.md`) and tool-use behavior.
- Receives telemetry, project README/context, and memory.
- Produces native tool calls only.

### 2.3 Scenario/project layer

- Each scenario is a real runnable project (possibly small), not an obvious demo/test fixture.
- Project docs and code should look like ordinary repository content.
- Bugs are not announced as “known benchmark bugs”; they are implied by normal project context and runtime evidence.

## 3. Scenario structure standard (target)

Each scenario directory should be shaped as:

```text
<scenario>/
  src/                 # only this is mounted into agent runtime container
    README.md          # ordinary human project README
    ...project files...
  tests/               # benchmark-only validators, hidden from agent
  scoring.json         # scenario scoring parameters for benchmark engine
  DESIGN.md            # maintainer-facing scenario design notes (hidden from agent)
```

Rules:

- `src/README.md` must read like a normal GitHub project README.
- Forbidden wording inside project-facing files: benchmark/testcase/agent/sandbox and similar meta-benchmark language.
- README/docs inside `src/` must not reveal the injected fault directly.

## 4. Agent runtime contract

- One wakeup = fresh conversation.
- Message order: `PROMPT.md` policy, then project README + MEMORY + telemetry.
- Assistant outputs one native `bash` tool call per turn.
- Terminals:
  - `everything_ok`
  - `escalate <level> <message>`
  - `escalate none <id_or_msg>`

## 5. PROMPT.md expectations

`PROMPT.md` is production-grade operator guidance, not benchmark narration.

It should:

- teach practical diagnosis/repair workflow for small models
- emphasize real shell execution, backup-before-mutation, manager-aware restart, delayed verification
- explain escalation philosophy (prefer safe escalation over risky guess)
- provide concrete, general, production-usable examples

It must not mention benchmark internals.

## 6. Telemetry and scheduling

- Host-wide strict telemetry object; no synthetic benchmark wrapper fields.
- Trend maps (`{timestamp:value}`) for metrics where temporal shape matters.
- Fixed-interval collection independent of model busy state.
- Latest-pending snapshot delivery when model is still busy.
- Archive: timestamped files + `latest.json` symlink.

## 7. Guardrails and rejections policy

- Keep hard-coded rejection logic minimal; put most behavior guidance in `PROMPT.md`.
- Hard bottom-line rejections remain for critical protocol violations (for example: missing tool call).
- Prefer extensible rejection configuration (for example regex-driven `rejections/` rules) for simple cases.
- Reserve hard-wired complex rejection logic for cross-command/semantic safety cases only.

## 8. Model endpoint expectations

- Reasoning default auto.
- Tiny-model repetition controls enabled.
- Sampling tuned for stability.
- GPU is allowed when available; CPU-only is explicit, not forced by default.

## 9. Output/schema stance

- No model output JSON schema; output channel is native tool calls.
- Telemetry input is validated on Python side.
