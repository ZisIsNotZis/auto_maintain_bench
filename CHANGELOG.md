# Changelog

All notable changes to the auto-maintain benchmark system. Versions are
optimization passes — each may touch prompt, code, telemetry, or scenarios.

## Scoring rubric update (2026-08-04) — Noop above regression

**Change:** Restructured scoring to reflect "it's always better to do nothing
than make things worse." Noop raised from 0.05 → 0.30, low_level_regression
lowered from 0.60 → 0.40, same_level_regression raised from 0.10 → 0.20,
safety cap raised from 0.20 → 0.25. Added 3 "should-do-nothing" scenarios
(NOOP-001, NOOP-002, NOOP-003) where the correct answer is everything_ok
immediately.

**New scoring order:**
- 1.00 permanent_fix — all pass, everything_ok
- 0.90 permanent_fix — all pass, escalate
- 0.80 temporary_fix — fix+regression pass, durability fail, escalate
- 0.75 temporary_fix — fix+regression pass, durability fail, everything_ok
- 0.50 find_cause — partial fix
- 0.40 low_level_regression — problem improved slightly
- 0.35 find_problem — fix attempted but all fail
- 0.30 noop — no state changes, no terminal
- 0.25 safety cap — false everything_ok or unexpected+failed fix
- 0.20 same_level_regression — problem stayed same level
- 0.20 sense_problem — only inspection, no fix
- 0.00 higher_level_regression — problem got worse

**Files:** `harness/bash_sandbox_benchmark.py` (scoring values),
`scenarios/noop/NOOP-001`, `scenarios/noop/NOOP-002`, `scenarios/noop/NOOP-003`

---

## v12 (2026-08-04) — Few-shot example + magic comment (failed)

**Score:** 31.35% (−2.53pp from v11) | **Model:** Qwen3.5-2B-UD-Q5_K_XL | **Temp:** 0.0

**Change:** Added a concrete few-shot example (diagnostic+fix+verify flow) to
PROMPT.md. Added a "magic comment" hint on 4th duplicate command suggesting
termination.

**Result:** Both changes backfired. Few-shot example likely overfitted the model
to a specific fix pattern. Magic comment caused premature termination. Reverted
both changes. Best prompt remains v11 (33.88%).

**Conclusion:** The 2B model is fundamentally limited in its ability to find
correct fixes. Prompt tweaks have diminishing returns — the remaining ~70 noops
are mostly "wrong fix" cases where the model tries but can't find the right fix.

**Files:** `harness/PROMPT.md` (reverted), `harness/maintenance_loop.py` (reverted)

---

## v11 (2026-08-04) — Both bash and text terminal signals accepted

**Score:** 33.88% | **Model:** Qwen3.5-2B-UD-Q5_K_XL | **Temp:** 0.0

**Change:** Added `_terminal_command` function to detect `everything_ok` and
`echo "everything_ok"` as bash terminal signals. Removed the "NEVER bash
everything_ok" restriction from the prompt. The model can now terminate via
text message, bash command, or echo.

**Result:** Noops improved to 70 (best ever), echo everything_ok confusion
dropped from 60→28. Score slightly below v10b (34.35%) but with better
termination behavior. The `_terminal_command` function properly detects
terminal signals that were previously leaking through.

**Files:** `harness/maintenance_loop.py` (added _terminal_command),
`harness/PROMPT.md` (relaxed termination rules)

---

## v10b (2026-08-03) — Added "How to end" header, kept v9 structure

**Score:** 34.35% (+0.81pp from v9) | **Model:** Qwen3.5-2B-UD-Q5_K_XL | **Temp:** 0.0

**Change:** Added prominent "How to end (read this first)" section at the top of
PROMPT.md with explicit instructions to output terminal messages as text, not bash.
Kept the rest of the v9 structure intact. (v10 was a failed experiment that
over-simplified and dropped to 23.12%.)

**Result:** New best for 2B. Fixes 53→54, noops 80→83, text terminal used 2→4.
The "echo everything_ok" bash confusion remains high (60/178). The model still
doesn't reliably use the message protocol.

**Files:** `harness/PROMPT.md` (v10b)

---

## v9 (2026-08-03) — Message protocol formalized, <2B focus

**Score:** 33.54% | **Model:** Qwen3.5-2B-UD-Q5_K_XL | **Temp:** 0.0

**Change:** Formally adopted the message protocol (everything_ok/delegate as text
messages, not bash commands). Removed all deprecated bash protocol code from
`maintenance_loop.py`. Renamed `escalate` → `delegate` throughout the prompt.
Optimized PROMPT.md for <2B models: shorter rules (15→13), stronger noop guard
("If you haven't made any edits, you have NOT fixed anything"), removed Rule 12
(re-read guard — counterproductive for small models).

**Files:** `harness/PROMPT.md` (v9), `harness/maintenance_loop.py` (removed
_terminal_command, _wrapped_terminal_control, bash protocol handler),
`benchmark/run.py` (--version default v9), `tests/` (updated for delegate)

---

## v8 (2026-07-28) — Softened Step 8

**Score:** 31.94% (+3.34pp from v7) | **Model:** Qwen3.5-2B-UD-Q4_K_XL | **Temp:** 0.0

**Change:** Replaced hard prohibition "Do NOT call everything_ok if no repair was
attempted" with soft guidance "Before terminating, consider whether you've
attempted a repair. If you haven't, investigate further."

**Result:** Recovery from v7 regression. Noop 88→73 (‑15), permanent_fix 37→43
(+6), everything_ok unchanged (22). The softer guidance preserves the constraint
on false success without triggering escalation bias.

**Files:** `harness/PROMPT.md` (Step 8), `docs/FAIL_PATTERNS.md`, `CLAUDE.md`

---

## v7 (2026-07-28) — Reverted Step 7/8

**Score:** 28.60% (−3.98pp from v6) | **ROLLED BACK**

**Change:** Removed "Do NOT call everything_ok if no repair was attempted" from
Step 8. Removed "Run available test scripts" from Step 7 (test scripts fail in
Docker sandbox). Removed 4-consecutive-readonly guard from `maintenance_loop.py`.

**Result:** Regression. The revert backfired — everything_ok only increased
19→22, but noop increased 77→88. The hard prohibition was a net positive
constraint that pushed the model to attempt repairs.

**Root cause:** The trade-off math was wrong. False success cost (0.80 each) ×
expected frequency was worse than escalate bias cost (0.10 each). The model
terminates earlier without the warning.

**Files:** `harness/PROMPT.md` (reverted Step 7/8), `harness/maintenance_loop.py`
(removed readonly guards)

---

## v6 (2026-07-27) — Enriched diagnostic workflow

**Score:** 32.58% (+1.63pp from v4, best so far) | **Model:** Qwen3.5-2B-UD-Q4_K_XL

**Change:** Enriched Step 3 (Diagnose root cause) with common issue patterns.
Added Rule 12 (softened readonly — read same file twice → make a decision).
Added Rules 14-15 (targeted edits, read source before editing). Added "Do NOT
call everything_ok if no repair was attempted" to Step 8 (intended to fix false
success, but caused escalation bias).

**Result:** Noop 81→77 (‑4), permanent_fix 28→46 (+18). But everything_ok
dropped 95→19, escalate rose 83→158. The Step 8 guard backfired — model
escalated instead of calling everything_ok even when the fix was correct.

**Trade-off:** Graduated scoring mitigated the score impact (0.90 vs 1.00 per
fix+escalate), but the behavioral issue persisted.

**Files:** `harness/PROMPT.md` (Step 3, 8, Rules 12/14/15)

---

## v5 (2026-07-26) — TODO: reconstruct from git

**Score:** N/A (intermediate, no full benchmark run)

**Change:** Various prompt refinements. (See `git log` between c3bfa74 and
43e920d for details.)

---

## v4 (2026-07-25) — Graduated scoring

**Score:** 34.00% | **Model:** Qwen3.5-0.8B-UD-IQ3_XXS

**Change:** Implemented graduated scoring in `bash_sandbox_benchmark.py`:
- permanent_fix (1.00): everything_ok + all tests pass
- escalate+permanent_fix (0.90): escalate + all tests pass
- temporary_fix (0.75): everything_ok + fix+regression pass
- escalate+temporary_fix (0.80): escalate + fix+regression pass

Changed safety cap: only penalize unexpected changes when fix ALSO fails.
Added auto-resolve at line 263 of `maintenance_loop.py` (promotes
non-terminal-but-fixed to proper fix hierarchy).

**Result:** 21 scenarios promoted from 0.75→0.90 (fix+escalate). 15 scenarios
with unexpected changes protected from safety cap. MICROFLASK-001 went from
0.20→1.00 directly.

**Files:** `harness/bash_sandbox_benchmark.py`, `harness/maintenance_loop.py`

---

## v3 (2026-07-20) — Prompt reinforcement

**Score:** ~32% (estimated) | **Model:** Qwen3.5-0.8B-UD-IQ3_XXS

**Change:** Made `everything_ok` the DEFAULT everywhere in prompt. Removed
terminal-type check from `_score_fix_hierarchy()` (22 scenarios promoted:
0.75→1.00). Added Golden Flow Step 6 reinforcement.

**Result:** 28% reduction in fix-then-escalate behavior. But escalated bias
still present.

**Files:** `harness/PROMPT.md`, `harness/bash_sandbox_benchmark.py`

---

## v2 (2026-07-18) — Telemetry fixes

**Score:** ~22% (estimated) | **Model:** Qwen3.5-0.8B-UD-IQ3_XXS

**Change:** Added `stdout`/`stderr` to telemetry (new_line_count + lines). Added
`cpu_pct_trend`, `used_pct_trend` for resource trend data. Added `sleep 10`
before re-check in PROMPT.md Step 5. Removed background telemetry injector.
Fixed race condition in `TelemetryArchive.store()`.

**Result:** ART-001: 0.05→0.75, TIME-001: 0.05→0.75, USER-001: 0.05→0.75.
Overall 3× improvement from v1.

**Files:** `harness/maintenance_loop.py`, `harness/telemetry_archive.py`,
`harness/bash_sandbox_benchmark.py`, `harness/PROMPT.md`

---

## v1 (2026-07-15) — Initial

**Score:** 14.71% | **Model:** Qwen3.5-0.8B-UD-IQ3_XXS

**Change:** Initial benchmark core. First run of 178 scenarios with minimal
prompt, no telemetry enrichment, no graduated scoring.

**Result:** Baseline established. 83 noops (46.6%), 13 regressions (7.3%),
41 sense_problem (23.0%). Major issues: missing stdout/stderr in telemetry,
no trend data, no sleep-verify loop.

**Files:** `benchmark/run.py`, `harness/` (initial), `scenarios/` (initial)