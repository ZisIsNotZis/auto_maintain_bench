Brainstorm: Making the Whole Project Better

Scenarios

Category consolidation — MEM/DISK/HEALTH all test "config value out of range" with different surface. Merge into 3 super-categories (Config, Runtime, Resource) with 4-5 distinct bug types each. Cleaner narrative for the paper. //organize is fine, but don't merge. We spent effort maintaining such huge number of working scenarios and it's our selling point.

Difficulty tiers — Tag every scenario easy/medium/hard based on model performance from v4:
- Easy (≥0.75 pass rate): MICROFLASK, TIME-, CFG- → ~30 scenarios
- Medium (0.25-0.75): DATA, CPU, ART, USER → ~50
- Hard (<0.25): MEM, NET, LOG, SEC, HEALTH, AGENT → ~98
This lets the paper say "model solves 60% of easy, 30% of medium, 5% of hard" instead of one flat number. //yes, I suggested to have smooth curve of difficulties before, from trivial
  to really hard (e.g. github real project but hide all testcase). You can clone/create/fork_and_modify_existing to have a smooth difficulty tiers.

Canary set — Pick 20 highest-correlation scenarios (e.g., CPU-003, TIME-002, CFG-005) that predict the full 178 score. Run these for 2-minute iteration cycles instead of the full 1-hour benchmark. Only run the full suite for final reporting. //yes

Scenario generator — The current patterns are: (1) pick a service config, (2) corrupt one value, (3) add telemetry pointing to it. Script-gen 1000+ variants from a template pool. Both evaluates the model more thoroughly and provides more training data. //interesting and important for future. But be more diverse and creative. If you think about it, we're trying to develop a maintainence agent that finds and fixes problems on actual production env. This is dead serious and should be useable to real world, so you should brainstorm about all kinds of problems that real world scenarios can happens, including real world diversity and software complexity. The goal is that test cases CAN be very hard and hidden, so that we can actually "discover" the true limits of models and design prompts and guide files specifically. In another word, it's a "generator" in terms of prompt and guideline for AI, not a program that generates buggy program.

Agent / Prompt

Few-shot examples — The current PROMPT.md is pure rules. Add 2 concrete examples showing the full chain (telemetry → read source → identify → fix → verify → terminate). The 2B model may pattern-match better from examples than from rules. Example format: //yes and no. Yes it do helps, but no it adds more context, makes edge tiny-llm use more CPU, and maybe dilute attention? A wired idea is you can have multiple "levels" of PROMPT.md just like JPEG's hierachical encoding?

## Example: Fix wrong config value
Telemetry says: "KeyError: 'mode' in app.py:42"
1. Read /sandbox/opt/demo-api/app.py line 42
2. See: `config['mode']` → needs `config.get('mode', 'serve')`
3. Fix with sed, restart, verify
4. everything_ok

Diagnostic scratchpad — Before fixing, the model writes:
Error source: /sandbox/etc/demo-api/health.env line 3
Root cause: HEALTH_MODE=off when it should be ok
Fix: sed -i 's/HEALTH_MODE=off/HEALTH_MODE=ok/' ...
This forces reasoning instead of guessing. Could be enforced by modifying the prompt or by a structured output schema. //Similar to 4, this may or maynot help, and could be a configurable part inside PROMPT.md (jinja?), which needs more experiments to verify. Currently we do have thinking trajectories, which is more or less this thing but without formattnig requirement.

Fine-tuning data from trajectories — Every v4 run produced a conversation transcript. The 53 auto-resolved trajectories are gold: the model fixed correctly but couldn't terminate. Fine-tune on these to teach the model the full cycle. Similarly, the 67 duplicate-loop trajectories show exactly where the model gets stuck. //yes this is a long time goal, and we should do that. I originally thought you already did this, if you didn't, you should. (DEFER this task to end of all tasks if not done)

Benchmark / Harness

Pre-baked Docker images — Current: each scenario builds a container from scratch (binds dirs, copies files). Pry with the scenario fixture baked in. Start time drops from 8-10s to <1s. GPU utilization goes from 29% →potentially 80%+. At concurrency=8, the full 178 could run in ~5 minutes. //bind mount takes zero time. In case of dependency though such as pip install or apt-get, we could have one or few golden image, if it do takes a lot of time. But ~5min is probably not a thing because we're running on a single 4090 with 4 parallelism. Things aren't going to be this fast. Measure actual data for preparation (including what it is doing) and report to be before making benchmark architecture complicated

Trajectory recorder — Add a --save-trajectories flag that writes the full message list per scenario. Currently  way to debug why a scenario failed without re-running. This is the single biggest missing debugging tool. //I thought we already have way to record trajectory don't we? Doesn't that work?

Auto-diagnosis of failures — After a run, automatically classify each failure into a FAIL_PATTERNS category by analyzing the trajectory. Currently we manually grep for symptoms. Could auto-detect: duplicate-loop, rejection-loop, noop, false-ok, escalate-bias. //not sure about the "auto" part. I don't think program can figure out why without hard-wiring some don't-make-sense rules. In terms of AI, yes, but this is more like a self-evolve meta thing in CLAUDE.md instructing how does this project self-evolve without human supervise.

Scenario pre-warm — Instead of create/destroy per scenario, keep a pool of 8 idle containers and recycle them. Use docker commit after setup, then docker run from the committed image for the next same-category run. //I don't think docker adds that much latency. Pre-baked docker images might be a thing, warn-up and dynamic attach/detach is probably not a thing, that's just too extreme and makes everything so complicated with negligible gain

Scoring

Efficiency metric — A scenario solved in 8 steps at 0.20 should score differently than one solved in 60 steps aiency multiplier: efficiency = min(1.0, optimal_steps / actual_steps). Penalizes 40-turn investigation loops. //Maybe token count instead of time, since our llama-server is saturated with multiple testcases and can't tell which services uses how much time. Also this should only be a tie breaker when they arrive at same enum score.

Backup compliance — Track whether .maint-backup was created before edits. If the model edits without backing up, apply a small penalty. Encourages safer behavior. //Okay-ish, but you have to very-clearly tell how to backup. In that sense, why don't the engine just back up for the llm in advance and delete backup after. Because the general rule of thumb is: Is something is must-look/read or must-do for whatever reason, unless not trivially doable, it should be done automatically by the engine

Per-category radar chart — Instead of one number, produce a radar chart across 5 axes: Config-read, Config-fix, Restart-verify, Multi-fault, Cleanup-terminate. Shows strengths and weaknesses at a glance. //That's a visulization thing and left for future discussion

Paper Strategy

The paper's contribution isn't "our model scores 34%" — that's weak. The contribution is:

1. Deterministic evaluation methodology — No LLM-as-judge, all points from observable effects. Reproducible, auditable, no prompt-leaking.
2. Graduated scoring rubric — Distinguishes "fix that escalates" from "fix that terminates correctly" from "fix Novel metric for autonomous agent evaluation.
3. Category-based failure taxonomy — A structured mapping of which maintenance tasks are easy/hard for small LMs. This is a dataset contribution: the 178 scenarios+taxonomy is reusable by anyone.
4. Safety-aware scoring — The safety cap (unexpected changes only penalized when fix also fails) is a principled approach to evaluation that doesn't punish exploration.

The narrative: "Edge-side tiny-LM host maintenance is feasible for simple config repairs (30-40%) but fails on multi-step diagnostics. Here is a reproducible platform to measure exactly which tasks and why."

Implementation: What to Do Before the Big Run

Let me recommend an order:

1. ✅ Prompt enrichment — Done
2. ✅ Code fixes — Done (readonly rule, duplicate counter)
3. Choose final temperature — temp=0.2 is reasonable
4. One canary scenario — pick one from each category for fast iteration
5. Full benchmark at temp=0.2 → baseline for comparison

And for the next iteration after the run:
- Pre-bake Docker images (biggest throughput gain available)
- Add trajectory logging (biggest debugging gain)
- Add few-shot examples to PROMPT.md
- Fine-tune on auto-resolved trajectories

---
Want to go ahead with the full benchmark at temp=0.2, or try any of these ideas first? The canary set approach al before committing to a 1-hour run.
