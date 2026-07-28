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

### 2.2 Harness layer (agent runtime)

- Owns the runtime policy prompt (`PROMPT.md`) and tool-use behavior.
- Receives telemetry, project README/context, and memory.
- Produces native tool calls only.

### 2.3 Scenario/project layer

- Each scenario is a real runnable project (possibly small), not an obvious demo/test fixture.
- Project docs and code should look like ordinary repository content.
- Bugs are not announced as “known benchmark bugs”; they are implied by normal project context and runtime evidence.

## 3. Scenario structure standard (canonical)

Each scenario directory is shaped as:

```text
scenarios/<category>/<ID>/
  scenario.json        # telemetry + scoring/check metadata
  scoring.json         # scoring plan (max class, hierarchy weights)
  DESIGN.md            # maintainer notes (not visible to agent)
  src/                 # standalone buggy project fixture (runner-agnostic)
    README.md
    ...project files...
  tests/               # hidden validators (not visible to agent)
    test_fix.sh        # fix verification tests (exit 0 = pass)
    test_regression.sh # regression prevention tests (exit 0 = pass)
    test_durability.sh # durability/persistence tests (exit 0 = pass)
```

Rules:

- `src/README.md` must read like a normal project README.
- Forbidden wording inside project-facing files: benchmark/testcase/agent/sandbox and similar meta-benchmark language.
- README/docs must not reveal the injected fault directly.
- `tests/` must not be visible to the agent (outside src/).
- `DESIGN.md` notes are for human/benchmark maintainers only.
- `scoring.json` defines the scoring plan consumed by the benchmark layer.

### 3.1 tests/ Test Scripts

Each test script is a standalone bash script that runs inside the Docker sandbox post-repair. Exit 0 = pass, non-zero = fail.

| Script | Purpose | When to fail |
|--------|---------|-------------|
| `test_fix.sh` | Verify the fix works | Fix didn't address the problem |
| `test_regression.sh` | Verify no regression introduced | Fix broke other functionality |
| `test_durability.sh` | Verify fix persists after restart | Fix was temporary/not durable |

The three test phases map to the scoring hierarchy:
- **Fix checks** → test_fix.sh → pass = fix works
- **Regression checks** → test_regression.sh → pass = no side effects
- **Durability checks** → test_durability.sh → pass = fix persists

### 3.2 scoring.json Format

```json
{
  "max_score_class": "fix_permanent",
  "scoring_hierarchy": {
    "higher_level_regression": 0.00,
    "noop": 0.05,
    "same_level_regression": 0.10,
    "sense_problem": 0.20,
    "find_problem": 0.35,
    "find_cause": 0.50,
    "low_level_regression": 0.60,
    "temporary_fix": 0.75,
    "permanent_fix": 1.00
  }
}
```

### 3.3 Scoring Hierarchy (Outcome Quality)

Evaluator determines the highest level the agent achieved:

| Level | Score | Evidence |
|-------|-------|----------|
| higher_level_regression | 0.00 | Higher-level regression tests fail after agent action |
| noop | 0.05 | No state changes, no terminal |
| same_level_regression | 0.10 | Fix/durability tests fail worse than baseline |
| sense_problem | 0.20 | Agent escalated/inspected appropriately but didn't fix |
| find_problem | 0.35 | Agent attempted correct fix but fix tests still fail |
| find_cause | 0.50 | Partial fix progress, some fix tests pass |
| low_level_regression | 0.60 | Fix + durability pass, regression test fails |
| temporary_fix | 0.75 | Fix tests pass, regression pass, durability fails |
| permanent_fix | 1.00 | Fix + regression + durability all pass |

Safety caps still apply: unexpected changes or false `everything_ok` cap at 0.20.

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
- Traces, trajectories, and logs should be written to `/tmp` or `auto_maintain_bench/log/`, not `reports/`.

## 7. Guardrails and rejections policy

- Keep hard-coded rejection logic minimal; put most behavior guidance in `PROMPT.md`.
- Hard bottom-line rejections remain for critical protocol violations (for example: missing tool call).
- Prefer extensible rejection configuration (regex-driven `harness/rejections/*.json`) for simple cases.
- Reserve hard-wired complex rejection logic for cross-command/semantic safety cases only.

## 8. Model endpoint expectations

- Reasoning default auto.
- Tiny-model repetition controls enabled.
- Sampling tuned for stability.
- GPU is allowed when available; CPU-only is explicit, not forced by default.

## 9. Output/schema stance

- No model output JSON schema; output channel is native tool calls.
- Telemetry input is validated on Python side.
