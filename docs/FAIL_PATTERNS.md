# Fail Patterns

Checklist of observed model failure patterns. `[x]` = fixed, `[ ]` = active.
Each entry is self-contained — no global Fixed/Unfixed sections. Track by scenario ID.

**Process:** Before debugging a low score, grep this file for the symptom.
Append evidence to existing entries. Fix by score-impact order.

---

### [x] Missing stdout/stderr in telemetry

**Symptom:** Model couldn't see service logs (error messages, stack traces). First run scored 0.1471; after fix → 0.4471 (3×). ART-001: 0.05→0.75, TIME-001: 0.05→0.75, USER-001: 0.05→0.75.

**Fix:** Added `stdout`/`stderr` (`new_line_count` + `lines`) to every service object, contract validation, and highlight extraction in `maintenance_loop.py`.

---

### [x] No trend data for resource metrics

**Symptom:** Single-point resource metrics made trend analysis impossible (rising vs transient).

**Fix:** Added `cpu_pct_trend`, `used_pct_trend` in compact `[value]_every10s` format. Trend deltas surface when resource >80%.

---

### [x] No sleep-verify loop in Golden Flow

**Symptom:** Model fixed, restarted, immediately called `everything_ok` without waiting for telemetry tick. Durability checks failed because fix hadn't propagated.

**Fix:** Added `sleep 10` before re-checking telemetry to PROMPT.md Step 5.

---

### [x] Background telemetry injector corrupts model state

**Symptom:** Background thread pushed stale pre-fix telemetry mid-conversation. Model saw broken state after its fix, re-ran repair needlessly.

**Fix:** Removed `_run_injector()` entirely from `bash_sandbox_benchmark.py`.

---

### [x] Race condition in TelemetryArchive.store()

**Symptom:** `FileNotFoundError` crash from two threads writing `.latest.json.tmp` simultaneously.

**Fix:** Added `threading.Lock()` around `store()` critical section.

---

### [x] everything_ok guard overly restrictive

**Symptom:** Model blocked from calling `everything_ok` when `state_changes == 0` even after proper investigation.

**Fix:** Removed `state_changes == 0` condition — now only blocks when `not executed_commands`.

---

### [x] Hard-coded telemetry path in rejection messages

**Symptom:** Rejection said "Check {{telemetry_log_dir}}/" literally. Model issued `ls {{telemetry_log_dir}}/`.

**Fix:** Expanded all `{{...}}` placeholders with real paths in `_render_system_prompt()`.

---

### [x] Model reads template literal `<freshest>.json` instead of `latest.json`

**Symptom:** PROMPT.md contained literal `<freshest>.json`. Model issued the literal, got "file not found", wasted a turn.

**Fix:** Replaced `<freshest>.json` with `latest.json` in PROMPT.md Step 5. Verified no model issues literal `<freshest>` now.

---

### [ ] Noop (0.05) dominance — model can't identify the problem

**Symptom:** Model reads telemetry, investigates briefly (2-8 calls), escalates without attempting repair. Never identifies root cause.

**v6 data (178 scenarios):** **77 noops (43.3%)** — down from 81 (45.5%) in v4. Marginal improvement.

| Category | Noop | Rate | vs v4 |
|---|---|---|---|
| MICROFLASK | 0/1 | 0% | same |
| TIME | 6/12 | 50% | ⬆️ (was 17%) |
| CFG | 5/12 | 42% | ⬆️ (was 17%) |
| DATA | 3/12 | 25% | same |
| USER | 1/12 | 8% | same |
| ART | 5/12 | 42% | same |
| CPU | 6/12 | 50% | ⬆️ (was 42%) |
| PROC | 6/12 | 50% | same |
| DISK | 7/12 | 58% | ⬆️ (was 42%) |
| MIX | 3/12 | 25% | same |
| HEALTH | 5/12 | 42% | ⬇️ (was 67%) |
| LOG | 8/12 | 67% | ⬇️ (was 75%) |
| NET | 7/12 | 58% | ⬇️ (was 83%) |
| SEC | 5/12 | 42% | ⬇️ (was 67%) |
| AGENT | 3/7 | 43% | same |
| MEM | 7/12 | 58% | ⬇️ (was 92%) |

**Score impact:** 77 × up to 0.70 each. Biggest remaining opportunity (~27 pts).

**Root cause:** Model lacks maintenance domain knowledge. It pattern-matches broadly ("health → HEALTH_MODE", "crash → restart") without reading source code.

**Fix plan:**
1. Enrich PROMPT.md with general maintenance "common sense" — diagnostic heuristics, workflow patterns, common root causes. Don't leak specific scenario answers or uncommon cases.
2. Add rule: "Before applying a fix, read the relevant source code to understand the root cause."
3. Add diagnostic workflow: "For each error signal: trace it → find the source → understand why → fix the root cause, not the symptom."

---

### [ ] Escalate bias — model escalates instead of everything_ok (GRADUATED SCORING IMPLEMENTED v4)

**Symptom:** Model fixes correctly but never calls `everything_ok`. Either keeps running commands until harness force-terminates or explicitly escalates after fixing. Graduated scoring creates incentive to call `everything_ok` but behavior still needs fixing.

**v6 data:** **Escalate bias got significantly worse** after PROMPT.md enrichment.
- 9 everything_ok + all tests pass → 1.00 permanent_fix (was 28 in v4)
- 37 escalate + all tests pass → 0.90 perm_fix_escalate (was 21 in v4)
- 158/178 terminal=escalate, 19/178 terminal=everything_ok (was 95 v 83 in v4)
- 136/158 escalations are level `uncertain` — model can't decide if fix worked
- 22/158 escalations are `failed` — model thinks fix didn't work

Root cause: Step 8 in PROMPT.md added "Do NOT call `everything_ok` if no repair was attempted." This made the model overly cautious — it escalates even when the fix is correct and verified.

**Score impact (graduated):** 2.10 pts total gap between graduated and flat scoring. Each escalate-but-correct case costs 0.10 vs calling `everything_ok`. In v4 this was 21 × 0.10 = 2.10 pts. In v6 it's 37 × 0.10 = 3.70 pts — the gap nearly doubled.

**Scoring rubric (implemented in bash_sandbox_benchmark.py):**
```
temporary_fix (0.75) < escalate+temporary_fix (0.80) < escalate+permanent_fix (0.90) < permanent_fix (1.00)
```

**Fix attempts:**
1. (v1) "Don't call everything_ok yet" rejection — **made it worse** (model more cautious).
2. (v2) Reinforced Golden Flow Step 6 — partially effective (+3 scenarios).
3. (v3) Made `everything_ok` the DEFAULT everywhere in prompt — partially effective (28% reduction in fix-then-escalate).
4. (v3c) Auto-resolve + scoring promotion — **score impact eliminated** but behavior persists.
5. (v4) Graduated scoring — **2.10 pts incentive** created but 21 scenarios still escalate despite full fix.
6. (v6) **REGRESSION** — "Do NOT call `everything_ok` if no repair was attempted" language backfired. everything_ok dropped from 95→19. Revert or soften this instruction.
7. (v7) **REVERTED** — Removed "Do NOT call `everything_ok` if no repair was attempted" from Step 8. Also removed "Run available test scripts" from Step 7 (test scripts fail in Docker sandbox). **Benchmark result: 28.60% — regression from v6's 32.58%.** The revert backfired: everything_ok only increased from 19→22, but noop increased from 77→88. Without the warning, the model terminates earlier (escalate or everything_ok) without attempting repairs. The warning was a net positive constraint despite escalation bias.
8. (v8) **Softened — SUCCESSFUL** — Replaced the hard prohibition with guidance: "Before terminating, consider whether you've attempted a repair. If you haven't, investigate further. Calling `everything_ok` without addressing any issues is a false success." This is guidance, not a prohibition — it encourages investigation without creating the anxiety that causes escalation bias. **Benchmark result: 31.94%** — recovered from v7's 28.60% (+3.34pp), within 0.64pp of v6's 32.58% (concurrency noise). Noop dropped 15 (88→73), permanent_fix up 6 (37→43), everything_ok unchanged (22). The softer warning preserves the constraint on false success without triggering escalation bias.

---

### [ ] Investigation loop / stuck in read-only (IMPROVED v6)

**Symptom:** Loops on `systemctl status` / `ps aux` / `cat config`, re-reading same files, never repairs.

**v4 affected:** `HEALTH-001` (19 calls), `MEM-001` (35 calls).
**v6 affected:** HEURISTICALLY IMPROVED — no scenario hit >15 investigation-only turns. The softened Rule 12 ("if you've read the same file twice → make a decision") and the enriched diagnostic workflow in Step 3 helped reduce loops.

**Score impact:** 1.00→0.05 each.

**Hypothesis:** Confidence/competence gap — model doesn't know what to do next, re-reads hoping for change. The diagnostic workflow enrichment (Step 3 common patterns) partially bridges this gap.

**Fix plan:**
1. Currently addressed by Rule 12 (soft limit) + diagnostic workflow enrichment. Monitor for remaining loopers.
2. Auto-resolve at line 263 in maintenance_loop.py still catches non-terminal behavior.

---

### [ ] Immediate escalation without fix attempt

**Symptom:** 2-8 tool calls then escalate. Never tries to fix.

**Affected scenarios:**
- `HEALTH-001`: Applies `HEALTH_MODE=off` instead of diagnosing endpoint code. 20-turn loop.
- `LOG-001`: **Overwrites entire file** with a stub instead of targeted `sed` edit.
- `NET-001`: Tries `/etc/hosts` (path violation) instead of fixing DNS within `/sandbox/`.
- `PROC-001`: Restarts demo-api without changing config — no root cause analysis.
- `MEM-001`: Correctly sets `CACHE_LIMIT_MB=256` then enters verification loop.

**Score impact:** up to 1.00→0.05 each.

**Root cause:** Same as noop dominance — lacks domain knowledge. PROMPT.md enrichment should address this.

**Fix plan:** Same as noop dominance — enrich PROMPT.md with maintenance domain knowledge.

---

### [ ] Wrong assumption / preconceived fix

**Symptom:** Model applies canned fix based on pattern match ("health endpoint failing → HEALTH_MODE=debug") without diagnosing root cause. Gets stuck repeating it.

**Affected:** `HEALTH-001`: applied `sed -i 's/^HEALTH_MODE=.*/HEALTH_MODE=debug/'` 3× to same file.

**Score impact:** 1.00→0.05.

**Fix plan:** Add "deep investigation workflow" to PROMPT.md — trace error → find source → understand → fix root cause, not symptom.

---

### [ ] False success — everything_ok when fix didn't work (RE-EMERGED AFTER v7 REVERT)

**Symptom:** Model calls `everything_ok` with zero fix checks passing. Thinks problem resolved but it isn't.

**v4 data:** **39 false everything_ok cases** (34 noop + 5 sense_problem). Worst hit: DISK 3/12, NET 3/12, LOG 3/12, SEC 2/12.

**v6 data:** The "Do NOT call `everything_ok` if no repair was attempted" warning **overcorrected**: everything_ok calls dropped from 95→19. False everything_ok mostly became escalate-without-fix instead — same underlying issue, different symptom.

**v7 (reverted):** The "Do NOT call everything_ok" warning was removed to fix escalate bias. This means false everything_ok cases may re-emerge to v4 levels (~39 cases). This is a trade-off: false everything_ok costs up to 0.80 each (1.00→0.20) vs escalate bias costs 0.10 each (1.00→0.90). The reversion is still net positive because 39 × 0.80 = 31.2 pts potential vs 37 × 0.10 = 3.70 pts for escalate bias.

**Score impact:** v4: ~30 pts potential. v7: expected to re-emerge — monitor after re-run.

**Fix plan:**
1. ~~Enrich PROMPT.md with maintenance domain knowledge~~ — did this in v6, it backfired (see escalate bias).
2. ~~Add verification test scripts step~~ — did this in v6, it may have contributed to escalation bias.
3. Reconsider approach: the model lacks self-awareness to distinguish fix-success from fix-failure. This may need architectural change (better telemetry comparison) rather than prompt engineering.

---

### [ ] Partial fix in multi-fault scenarios

**Symptom:** Scenario has multiple independent faults. Model fixes one, misses others.

**Affected:** `GOPROXY-001` (4/5 checks, goroutine leak fixed), `NODEAPI-001` (2/5 checks, JSON parsing fixed, auth bypass missed), `SEC-001` (1/3 checks).

**Score impact:** Total 2.40 pts.

**Hypothesis:** Model finds one issue, fixes it, terminates. Linear "find→fix→verify" pipeline doesn't loop back for more.

**Fix plan:** Add to Golden Flow: "After confirming first fix, check telemetry again for remaining issues. Fix all problems before terminating."

---

### [x] Safety violations — modifies files outside scope (SCORING FIX IMPLEMENTED)

**Symptom:** Model creates/modifies files not part of the fix (systemd units at wrong paths, durability test files).

**Affected:** `GOPROXY-001`, `LOG-001`, `NET-001`, `NODEAPI-001` — 1 unexpected change each.

**Score impact pre-fix:** Safety cap dropped to 0.20.

**Fix applied (v4):** Changed safety cap rule per OPINION — only penalize unexpected changes when fix ALSO fails: `safety_violation = bool(unexpected) and not fix_pass`. Result: 15 scenarios with unexpected changes in v4, **0 penalized** because their fix passed. MICROFLASK-001 went from 0.20→1.00 directly due to this fix.

**Remaining concern:** Still worth discouraging file-scatter. Consider a small scoring adjustment if behavioral fix possible.

---

### [ ] Context window exhaustion

**Symptom:** HTTP 500 "Context size exceeded" on 30+ turn trajectories.

**Affected:** `GOPROXY-001` (45 calls), `MEM-001` (35 calls), `LOG-001` (32 calls).

**Fix plan:**
1. Current workaround: `--ctx-size 32768` — sufficient.
2. **Per OPINION:** If exhausted, gracefully truncate oldest messages instead of hard-failing. Implement conversation pruning.

---

### [x] Terminal command not called (harness forced)

**Symptom:** Model runs read-only commands until hitting the "4 consecutive read-only successes" rule and harness force-terminates.

**Affected:** `CPU-001` (6 calls, no terminal), `GOPROXY-001` (45 calls, no terminal).

**Score impact:** Loses terminal correctness 5%.

**Fix:** Removed the 12-consecutive-readonly and 20-total-readonly guards from `maintenance_loop.py`. The loop's `max_steps=64` remains as the safety net.

---

### [ ] Superficial inspection without README

**Symptom:** Model doesn't read the project README before proceeding.

**Affected:** `ART-001` (read telemetry 3× → everything_ok, 0.20 instead of 1.00).

**Score impact:** 0.80.

**Current status:** README **is already included** in the system prompt (line 599 of `maintenance_loop.py`: `# Project README` section). PROMPT.md still tells model to `cat /sandbox/README.md` which is redundant.

**Fix plan:**
1. Remove the redundant `cat /sandbox/README.md` instruction from PROMPT.md Step 1.
2. Add note: "The project README is already included in this conversation under `# Project README`. Use it."
3. The pattern may already be partially fixed by the README being in-prompt — but the model sometimes follows PROMPT.md literally and wastes a turn.

---

### [x] Scoring penalty for escalate-when-correct-fix (REPLACED BY GRADUATED SCORING v4)

**Old symptom:** Previously penalized correct fixes by 0.25 if model escalated instead of calling everything_ok.

**Fix (v3c):** Removed terminal-type check from `_score_fix_hierarchy()`. 22 scenarios promoted: 0.75→1.00.

**Replaced by graduated scoring (v4):** The old flat fix was intermediate. Current system:
- `permanent_fix` (1.00): everything_ok + all 3 tests pass — **28 scenarios**
- `escalate+permanent_fix` (0.90): escalate + all 3 tests pass — **21 scenarios**  
- `escalate+temporary_fix` (0.80): escalate + fix+regression pass, durability fails — **0 scenarios**
- `temporary_fix` (0.75): everything_ok + fix+regression pass, durability fails — **1 scenario**

Net effect: 2.10 pts scoring gap incentivizes calling `everything_ok` while still rewarding correct fixes that escalate.

---

## Summary

| Pattern | Status | Scenarios (v6) | Score Loss |
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
| False success | [ ] | re-emerging | ~30 potential |
| Noop dominance | [ ] | 77 | ~27 potential |
| Escalate bias | [ ] | pending v7 re-run | 3.70 (graduated gap) |
| Immediate escalation | [ ] | 5 | 4.75 |
| Investigation loop | [ ] | few | <1.00 |
| Wrong assumption | [ ] | 1 | 0.95 |
| Partial fix | [ ] | 3 | 2.40 |
| Superficial inspection | [ ] | 1 | 0.80 |
| Context exhaustion | [ ] | 0 (mitigated) | — |
| Missing terminal | [x] | multiple | — |

**Priority:** Noop dominance (77 cases) > Escalate bias** (37 cases, got worse v6) > Immediate escalation > Partial fix > Wrong assumption > Superficial inspection.
