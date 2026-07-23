# Future Trigger Engine

## Current scheduling

The maintenance daemon collects telemetry on a fixed schedule (default 10
seconds) regardless of model state. While a cycle is still running, newly
collected snapshots are not injected mid-cycle; only the newest pending
snapshot is delivered to the next cycle.

Scheduling is daemon control state, not maintenance evidence, so the wakeup
signal contains no round number, elapsed time, or trigger field.

## Future design

A future trigger engine may wake the daemon earlier than the fixed poll. It is
not implemented in the current scope.

Each trigger would be a daemon-managed rule with:

- a stable name;
- an enabled boolean;
- a long-running or long-poll command;
- an execution timeout;
- a minimum interval;
- bounded stdout used as the wake reason;
- captured exit status and stderr for diagnostics.

Initial installations may provide common host and service triggers. Models or
agents may later use validated tools to add, modify, enable, disable, or delete
triggers.

Trigger commands must run with restricted privileges, bounded output, explicit
resource limits, and no shell interpolation from model-provided values.

The trigger engine should affect wakeup timing and future latency scoring, but
its internal configuration should not be copied into every telemetry payload.
