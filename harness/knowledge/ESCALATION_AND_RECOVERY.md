# Escalation and Recovery

## The Fix-Verify-Revert Cycle

1. **Apply** one targeted fix
2. **Restart** the service: `systemctl restart <service-name>`
3. **Wait**: `sleep 10` — let the next telemetry tick arrive
4. **Verify**: `cat _harness/telemetry/latest.json` — check service state, health, stderr, events
5. **Decide**:
   - **Fully fixed** → `everything_ok`
   - **Significantly better** (partial fix: severity reduced, but not fully resolved) → keep the change, look for the remaining issue
   - **No change** → **REVERT** the change. Try a DIFFERENT approach.
   - **Worse** (new errors, higher resource usage, additional services failing) → **REVERT immediately**. Then try something else.

## Reverting Changes

If your fix didn't help or made things worse, restore the original:
- If you used sed: `sed -i 's/^KEY=new_value/KEY=old_value/' file`
- If you used heredoc: rewrite the original content (you should have read it first)
- If you made a backup: `cp file.maint-backup file`

## When to Keep Trying

You should try a different approach when:
- Your first fix was based on a wrong hypothesis
- You now understand the problem better after seeing the result
- There's another config file or setting you haven't checked yet
- The error message suggests a different root cause than you initially thought
- Multiple approaches exist to solve the same problem (e.g., reduce workers vs. increase timeout vs. enable caching)

## When to Escalate

Use `delegate <level> <message>` ONLY when:
- **uncertain**: You have read the source code at the error location and cannot determine what would fix it, even after trying to understand the logic
- **unlocated**: The telemetry shows an error but you cannot find where the error originates (no file/line reference, search didn't find the source)
- **no_fix**: Root cause identified but cannot be fixed by editing config files under /sandbox/ (needs package install, kernel parameter, external service, hardware change, etc.)
- **failed**: You have tried at least TWO different approaches, both correctly applied and verified, and the problem persists
- **blocked**: Required file is missing or required command is not available in the sandbox

## When to Use everything_ok

Use everything_ok ONLY when ALL of these are true:
- You have made at least one edit to a file
- The service is running and healthy
- No new error events in telemetry
- Resource pressure is normal (CPU < 80%, memory < 80%, disk < 80%)
- You have checked telemetry after the fix (waited 10s and verified at least twice)

## Common Mistakes

- Calling everything_ok without checking telemetry after the fix
- Calling everything_ok when the service is still unhealthy
- Escalating after a successful fix — check telemetry first!
- Escalating after ONE failed attempt without trying a different approach
- Keeping a bad fix that made things worse instead of reverting
- Not reading stderr lines — they contain the actual error messages
- Looping: running the same check command repeatedly without changing anything
- Forgetting to restart the service after editing config