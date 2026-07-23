# Use a strict host-wide wakeup contract

The maintenance daemon sends a timestamped, bounded snapshot containing
flattened host resources, all managed services, per-service output deltas and
events, network interfaces, notable processes, host events, and explicit
collection errors. Scheduling and benchmark concepts are excluded; every
object rejects unknown properties so changes remain deliberate.
