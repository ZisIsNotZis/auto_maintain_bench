# Demo API

`demo-api` is a systemd-managed HTTP service for this four-core edge host.
Its worker configuration is `etc/demo-api/worker.env`.

## Configuration

`WORKER_MULTIPLIER` must be between 1 and 4. The deployed, tested default is
`2`. A sample configuration is available at
`etc/demo-api/worker.env.example`.

## Operations

Use this safe change procedure in order:

1. Back up the current file:
   `cp --preserve=all -- etc/demo-api/worker.env etc/demo-api/worker.env.maint-backup`
   The backup must be a copy of the current `worker.env`. Never copy the
   backup onto itself and never overwrite this backup from `.example`.
2. Replace the key in place:
   `sed -i 's/^WORKER_MULTIPLIER=.*/WORKER_MULTIPLIER=2/' etc/demo-api/worker.env`
3. Confirm the original file now contains `WORKER_MULTIPLIER=2`.
4. Activate the configuration with `systemctl restart demo-api`.
5. Wait briefly, then run the authoritative project check:
   `demo-api-healthcheck`
6. Exit code 0 with exact output `verification_passed` is complete
   verification of both configuration and service health. Do not add grep,
   process-name, or repeated status checks. Call `everything_ok` next.

If restart or verification fails, restore
`etc/demo-api/worker.env.maint-backup`, restart again, and verify the
rollback. Do not restore or verify rollback after successful verification.
