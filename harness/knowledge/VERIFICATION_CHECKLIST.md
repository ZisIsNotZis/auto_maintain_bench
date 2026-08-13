# Verification Checklist

## After Every Fix, Run These Checks:

1. **Did you actually edit a file?** If not, you haven't fixed anything.
2. **Did you restart the service?** Config changes only take effect after restart.
3. **Did you wait?** `sleep 10` — let the next telemetry tick arrive.
4. **Check the latest telemetry**: `cat _harness/telemetry/latest.json`

## What to Check in Telemetry

- **Service state**: should be "running" (not "failed", "stopped", "crashed")
- **Service health**: should be "healthy" (not "unhealthy", "degraded")
- **stderr**: should have no new error lines since your fix
- **Events**: should have no new critical or error events
- **Resource pressure**: CPU, memory, disk should be below warning thresholds
- **Notable processes**: should not show unexpected high-resource processes

## If the Fix Didn't Work

1. **Confirm the edit**: `cat` the file you edited — is the change there?
2. **Confirm the restart**: `systemctl status <service>` — is it running?
3. **Diagnose the new state**: Did the error change? A new error message = progress, you found one layer.
4. **Revert**: If the fix made things worse or had no effect, restore the original immediately.
5. **Retry**: Try a different approach based on what you learned from the failure.
6. **Escalate**: Only after trying at least two different approaches that both failed.

## If the Fix Worked

1. **Multiple checks**: Verify at least twice (wait 10s, check, wait 10s, check again). Transient success can be misleading.
2. **Check for regressions**: Did fixing one problem break something else? Check all services.
3. **All services**: If there are multiple services, check ALL of them — not just the one you fixed.
4. **Resource trends**: Look at trend data to confirm the fix is sustained, not just a transient dip.
5. **Final decision**: Only `everything_ok` when ALL problems are resolved.

## Common Verification Mistakes

- **Checking telemetry before restart**: The fix hasn't taken effect yet. Restart first, then check.
- **Not waiting long enough**: `sleep 10` is needed for the telemetry tick to capture the new state.
- **Checking only one metric**: The service might be running but unhealthy. Check state AND health.
- **Ignoring stderr**: New errors in stderr mean something is still broken, even if the service is running.
- **Ignoring events**: Host-level events (network, disk, OOM) can indicate problems that service telemetry doesn't show.
- **False equivalence**: "The service is running" ≠ "The problem is fixed". Check health, stderr, and resource usage.
- **Single check**: One clean telemetry snapshot might be lucky timing. Check twice.