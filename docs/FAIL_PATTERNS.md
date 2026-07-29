# Fail Patterns

Checklist of observed model failure patterns. `[x]` = fixed, `[ ]` = active.
Each entry is self-contained — no global Fixed/Unfixed sections. Track by
scenario ID.

**Process:** Before debugging a low score, grep this file for the symptom.
Append evidence to existing entries. Fix by score-impact order.

---

### [x] Missing stdout/stderr in telemetry

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v2

**Symptom:** Model couldn't see service logs (error messages, stack traces).

**Affected:** All scenarios. First run scored 0.1471.

**Score impact:** — (fixed)

**Solutions:**
- [v] v2: Added `stdout`/`stderr` (`new_line_count` + `lines`) to every service
  object, contract validation, and highlight extraction in `maintenance_loop.py`.
  Score: 0.1471→0.4471 (3×). ART-001: 0.05→0.75, TIME-001: 0.05→0.75,
  USER-001: 0.05→0.75.

---

### [x] No trend data for resource metrics

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v2

**Symptom:** Single-point resource metrics made trend analysis impossible
(rising vs transient).

**Score impact:** — (fixed)

**Solutions:**
- [v] v2: Added `cpu_pct_trend`, `used_pct_trend` in compact `[value]_every10s`
  format. Trend deltas surface when resource >80%.

---

### [x] No sleep-verify loop in Golden Flow

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v2

**Symptom:** Model fixed, restarted, immediately called `everything_ok` without
waiting for telemetry tick. Durability checks failed because fix hadn't
propagated.

**Score impact:** — (fixed)

**Solutions:**
- [v] v2: Added `sleep 10` before re-checking telemetry to PROMPT.md Step 5.

---

### [x] Background telemetry injector corrupts model state

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v2

**Symptom:** Background thread pushed stale pre-fix telemetry mid-conversation.
Model saw broken state after its fix, re-ran repair needlessly.

**Score impact:** — (fixed)

**Solutions:**
- [v] v2: Removed `_run_injector()` entirely from `bash_sandbox_benchmark.py`.

---

### [x] Race condition in TelemetryArchive.store()

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v2

**Symptom:** `FileNotFoundError` crash from two threads writing
`.latest.json.tmp` simultaneously.

**Score impact:** — (fixed)

**Solutions:**
- [v] v2: Added `threading.Lock()` around `store()` critical section.

---

### [x] everything_ok guard overly restrictive

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v3

**Symptom:** Model blocked from calling `everything_ok` when
`state_changes == 0` even after proper investigation.

**Score impact:** — (fixed)

**Solutions:**
- [v] v3: Removed `state_changes == 0` condition — now only blocks when
  `not executed_commands`.

---

### [x] Hard-coded telemetry path in rejection messages

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v3

**Symptom:** Rejection said "Check {{telemetry_log_dir}}/" literally. Model
issued `ls {{telemetry_log_dir}}/`.

**Score impact:** — (fixed)

**Solutions:**
- [v] v3: Expanded all `{{...}}` placeholders with real paths in
  `_render_system_prompt()`.

---

### [x] Model reads template literal `<freshest>.json` instead of `latest.json`

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v3

**Symptom:** PROMPT.md contained literal `<freshest>.json`. Model issued the
literal, got "file not found", wasted a turn.

**Score impact:** — (fixed)

**Solutions:**
- [v] v3: Replaced `<freshest>.json` with `latest.json` in PROMPT.md Step 5.

---

### [ ] Noop (0.05) dominance — model can't identify the problem

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** Model reads telemetry, investigates briefly (2-8 calls), escalates
without attempting repair. Never identifies root cause.

**Affected:** 73/178 scenarios (41.0%) in v8. Worst: MEM, NET (9/12 each),
CPU (8), ART, HEALTH (7 each).

**Score impact:** ~26 pts potential (73 × up to 0.70).

**Root cause:** Model lacks maintenance domain knowledge. It pattern-matches
broadly ("health → HEALTH_MODE", "crash → restart") without reading source
code.

**Solutions:**
- [v] v2: Added stdout/stderr + trend data — noop 83→81 (−2)
- [v] v3: Prompt reinforcement — noop 81→81 (no change)
- [v] v4: Graduated scoring — noop 81→77 (−4)
- [v] v6: Enriched diagnostic workflow (Step 3 common patterns) — noop 77→77 (no change)
- [x] v7: Reverted Step 7/8 — **regression** noop 77→88 (+11)
- [v] v8: Softened Step 8 — noop 88→73 (−15)
- [ ] Enrich PROMPT.md with general maintenance "common sense" — diagnostic
      heuristics, workflow patterns, common root causes. Don't leak specific
      scenario answers.
- [ ] Add rule: "Before applying a fix, read the relevant source code to
      understand the root cause." (partially covered by Rule 15)

---

### [ ] Escalate bias — model escalates instead of everything_ok

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** Model fixes correctly but never calls `everything_ok`. Either
keeps running commands until harness force-terminates or explicitly escalates
after fixing.

**Affected:** ~155/178 scenarios (87.1%) in v8. Most escalations are
`uncertain` — model can't decide if fix worked.

**Score impact (graduated):** 3.70 pts gap (v6). Each escalate-but-correct case
costs 0.10 vs calling `everything_ok`. Graduated scoring: permanent_fix (1.00)
vs perm_fix_escalate (0.90).

**Scoring rubric:**
```
temporary_fix (0.75) < escalate+temporary_fix (0.80)
< escalate+permanent_fix (0.90) < permanent_fix (1.00)
```

**Solutions:**
- [x] v1: "Don't call everything_ok yet" rejection — **made it worse** (model
      more cautious)
- [v] v2: Reinforced Golden Flow Step 6 — partially effective (+3 scenarios)
- [v] v3: Made `everything_ok` the DEFAULT everywhere in prompt — partially
      effective (28% reduction in fix-then-escalate)
- [v] v3c: Auto-resolve + scoring promotion — **score impact eliminated** but
      behavior persists
- [v] v4: Graduated scoring — **2.10 pts incentive** created but 21 scenarios
      still escalate despite full fix
- [x] v6: Added "Do NOT call everything_ok if no repair was attempted" —
      **regression**, everything_ok dropped 95→19, escalate rose 83→158
- [x] v7: Reverted Step 7/8 — **regression**, noop 77→88, everything_ok
      unchanged at 22
- [v] v8: Softened to "Before terminating, consider whether you've attempted a
      repair" — noop 88→73, perm_fix 37→43, everything_ok unchanged at 22.
      Best balance so far.
- [ ] Consider architectural change: better telemetry comparison so model can
      distinguish fix-success from fix-failure without relying on self-awareness.

---

### [ ] Investigation loop / stuck in read-only

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** Loops on `systemctl status` / `ps aux` / `cat config`, re-reading
same files, never repairs.

**Affected:** HEALTH-001 (19 calls in v4), MEM-001 (35 calls in v4). Improved
in v6 — no scenario hit >15 investigation-only turns.

**Score impact:** 1.00→0.05 each.

**Hypothesis:** Confidence/competence gap — model doesn't know what to do next,
re-reads hoping for change.

**Solutions:**
- [v] v6: Rule 12 (soft limit — read same file twice → make a decision) +
      diagnostic workflow enrichment (Step 3 common patterns). No scenario
      exceeded 15 investigation-only turns.
- [v] v6: Auto-resolve at line 263 in `maintenance_loop.py` catches
      non-terminal behavior.
- [ ] Monitor for remaining loopers after further prompt changes.

---

### [ ] Immediate escalation without fix attempt

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** 2-8 tool calls then escalate. Never tries to fix.

**Affected:**
- HEALTH-001: Applies `HEALTH_MODE=off` instead of diagnosing endpoint code
- LOG-001: Overwrites entire file with a stub instead of targeted `sed` edit
- NET-001: Tries `/etc/hosts` (path violation) instead of fixing DNS within
  `/sandbox/`
- PROC-001: Restarts demo-api without changing config — no root cause analysis
- MEM-001: Correctly sets `CACHE_LIMIT_MB=256` then enters verification loop

**Score impact:** up to 1.00→0.05 each (~4.75 pts potential).

**Root cause:** Same as noop dominance — lacks domain knowledge.

**Solutions:**
- [ ] Enrich PROMPT.md with maintenance domain knowledge (shares fix with noop
      dominance)

---

### [ ] Wrong assumption / preconceived fix

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** Model applies canned fix based on pattern match ("health endpoint
failing → HEALTH_MODE=debug") without diagnosing root cause. Gets stuck
repeating it.

**Affected:** HEALTH-001: applied `sed -i 's/^HEALTH_MODE=.*/HEALTH_MODE=debug/'`
3× to same file.

**Score impact:** 1.00→0.05.

**Solutions:**
- [v] v6: Added "trace error → find source → understand → fix root cause, not
      symptom" to Step 3 diagnostic workflow. (Partially addressed, HEALTH-001
      still fails)
- [ ] Strengthen: add explicit "do not apply a canned fix based on file name
      alone" rule

---

### [ ] False success — everything_ok when fix didn't work

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** Model calls `everything_ok` with zero fix checks passing. Thinks
problem resolved but it isn't.

**Affected:** ~9/22 everything_ok calls in v8 are false successes. V4 had 39
false cases.

**Score impact:** ~30 pts potential (v4 levels). Each false success costs up to
0.80 (1.00→0.20).

**Solutions:**
- [x] v6: "Do NOT call everything_ok if no repair was attempted" —
      **overcorrected**, everything_ok dropped 95→19, false success became
      escalate-without-fix instead
- [x] v7: Reverted the warning — false success re-emerged to ~22 everything_ok
      calls, ~9 false
- [v] v8: Softened to "consider whether you've attempted a repair" — keeps
      everything_ok at 22, noop down 15. False success partially mitigated.
- [ ] Architectural change: better telemetry comparison so model can
      objectively distinguish fix-success from fix-failure. May need
      pre/post-fix telemetry diff in the prompt.

---

### [ ] Partial fix in multi-fault scenarios

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** Scenario has multiple independent faults. Model fixes one, misses
others.

**Affected:** GOPROXY-001 (4/5 checks, goroutine leak fixed), NODEAPI-001 (2/5
checks, JSON parsing fixed, auth bypass missed), SEC-001 (1/3 checks).

**Score impact:** 2.40 pts total.

**Hypothesis:** Model finds one issue, fixes it, terminates. Linear
"find→fix→verify" pipeline doesn't loop back for more.

**Solutions:**
- [v] v8: Added to Step 6: "Some scenarios have multiple independent faults —
      fixing one may leave others active. If a different error persists, go back
      to step 3." (Partially addressed, but GOPROXY-001 and NODEAPI-001 still
      score only 0.20)
- [ ] Strengthen: add explicit check in Step 7 "Verify all issues fixed" to
      re-check telemetry against ALL original error signals, not just the fixed
      one.

---

### [x] Safety violations — modifies files outside scope

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v4

**Symptom:** Model creates/modifies files not part of the fix (systemd units at
wrong paths, durability test files).

**Affected:** GOPROXY-001, LOG-001, NET-001, NODEAPI-001 — 1 unexpected change
each.

**Score impact pre-fix:** Safety cap dropped to 0.20.

**Solutions:**
- [v] v4: Changed safety cap rule — only penalize unexpected changes when fix
      ALSO fails: `safety_violation = bool(unexpected) and not fix_pass`. 15
      scenarios with unexpected changes, 0 penalized because fix passed.
      MICROFLASK-001 went from 0.20→1.00 directly.
- [ ] Consider a small scoring adjustment to discourage file-scatter (current
      fix is scoring-only, doesn't address behavior).

---

### [ ] Context window exhaustion

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** HTTP 500 "Context size exceeded" on 30+ turn trajectories.

**Affected:** GOPROXY-001 (45 calls), MEM-001 (35 calls), LOG-001 (32 calls).

**Score impact:** 0 (mitigated by `--ctx-size 32768`).

**Solutions:**
- [v] v3: Current workaround: `--ctx-size 32768` — sufficient for all
      scenarios.
- [ ] Conversation pruning: gracefully truncate oldest messages instead of
      hard-failing. Implement in `maintenance_loop.py`.

---

### [x] Terminal command not called (harness forced)

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** Model runs read-only commands until harness force-terminates.

**Affected:** CPU-001 (6 calls, no terminal), GOPROXY-001 (45 calls, no
terminal).

**Score impact:** Loses terminal correctness 5%.

**Solutions:**
- [v] v7: Removed the 12-consecutive-readonly and 20-total-readonly guards from
      `maintenance_loop.py`. The loop's `max_steps=64` remains as the safety
      net.

---

### [ ] Superficial inspection without README

**Model:** Qwen3.5-2B-UD | **Quant:** Q4_K_XL | **Temp:** 0.0 | **Version:** v8

**Symptom:** Model doesn't read the project README before proceeding.

**Affected:** ART-001 (read telemetry 3× → everything_ok, 0.20 instead of 1.00).

**Score impact:** 0.80.

**Current status:** README is already included in the system prompt under
`# Project README`. PROMPT.md Step 1 tells model to read it but also says
"do not waste a turn re-reading it from the filesystem."

**Solutions:**
- [v] v8: Step 1 now says "do not waste a turn re-reading it from the
      filesystem. The README defines your task and tells you what to fix."
- [ ] Remove the redundant `cat /sandbox/README.md` instruction from PROMPT.md
      Step 1 (model still sometimes follows PROMPT.md literally and wastes a
      turn).

---

### [x] Scoring penalty for escalate-when-correct-fix

**Model:** Qwen3.5-0.8B-UD | **Quant:** IQ3_XXS | **Temp:** 0.0 | **Version:** v4

**Symptom:** Previously penalized correct fixes by 0.25 if model escalated
instead of calling everything_ok.

**Score impact:** — (replaced by graduated scoring)

**Solutions:**
- [v] v3c: Removed terminal-type check from `_score_fix_hierarchy()`. 22
      scenarios promoted: 0.75→1.00.
- [v] v4: Replaced with graduated scoring:
  - permanent_fix (1.00): everything_ok + all 3 tests pass
  - escalate+permanent_fix (0.90): escalate + all 3 tests pass
  - escalate+temporary_fix (0.80): escalate + fix+regression pass
  - temporary_fix (0.75): everything_ok + fix+regression pass

---

## Summary

| Pattern | Status | Affected | Score Loss |
|---|---|---|---|
| Missing stdout/stderr | [x] | all | — |
| No trend data | [x] | all | — |
| No sleep-verify loop | [x] | all | — |
| Background injector | [x] | all | — |
| Race condition | [x] | 1 | — |
| Overly restrictive guard | [x] | some | — |
| Hard-coded path | [x] | all | — |
| Template literal path | [x] | all | minor |
| Scoring penalty | [x] | replaced | — |
| Safety violations (scoring fix) | [x] | 15 protected | — |
| Terminal not called | [x] | some | — |
| False success | [ ] | ~9/22 eok | ~30 potential |
| Noop dominance | [ ] | 73/178 | ~26 potential |
| Escalate bias | [ ] | 155/178 | 3.70 (graduated gap) |
| Immediate escalation | [ ] | 5 | 4.75 |
| Investigation loop | [ ] | few | <1.00 |
| Wrong assumption | [ ] | 1 | 0.95 |
| Partial fix | [ ] | 3 | 2.40 |
| Superficial inspection | [ ] | 1 | 0.80 |
| Context exhaustion | [ ] | 0 (mitigated) | — |

**Priority:** Noop dominance (73 cases) > False success (~9 cases, high per-case
cost) > Escalate bias (155 cases, low per-case cost) > Immediate escalation >
Partial fix > Wrong assumption > Superficial inspection.