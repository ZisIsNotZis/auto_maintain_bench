# Host Maintenance

This context describes the production daemon that maintains one edge host and
the services managed on that host.

## Language

**Maintenance daemon**:
The resident host process that collects telemetry, invokes the model, validates
tool calls, and applies permitted maintenance operations.
_Avoid_: Agent, runner

**Wakeup signal**:
A bounded factual snapshot collected on the daemon's fixed periodic scheduler.
Collection continues regardless of model busy state; only the newest pending
snapshot is delivered when the next cycle starts.
_Avoid_: Round, tick, observation event

**Managed service**:
A systemd unit, container, or supervised process whose lifecycle and resource
usage are monitored by the maintenance daemon.
_Avoid_: App, worker

**Collector integrity**:
Structured collection errors identifying telemetry that could not be obtained.
The maintenance daemon itself appears as a managed service.
_Avoid_: Collector object, telemetry confidence

**Host event**:
A bounded, deduplicated operational fact from the kernel or host. Events owned
by a managed service remain under that service.
_Avoid_: Raw log

**Notable process**:
A non-service process included because it is abnormal or consumes significant
resources, such as a zombie or process in uninterruptible sleep.
_Avoid_: Process inventory
