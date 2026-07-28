# Demo API

`demo-api` is a systemd-managed service. Temporary upload cache files are
stored under `./var/tmp/demo-cache`. They are disposable after an
upload fails or completes; persistent application data is stored elsewhere.

## Retention

`etc/demo-api/retention.env` controls automatic cache retention.
`RETENTION_ENABLED=true` is the supported durable setting.

## Operations

Use this exact sequence, with no extra checks or substitutions:

1. `cp --preserve=all -- etc/demo-api/retention.env etc/demo-api/retention.env.maint-backup`
2. `find ./var/tmp/demo-cache -type f | sort > ./var/tmp/demo-cache.maint-backup-list`
3. `find ./var/tmp/demo-cache -type f -delete`
4. `sed -i 's/^RETENTION_ENABLED=.*/RETENTION_ENABLED=true/' etc/demo-api/retention.env`
5. `systemctl restart demo-api`
6. `sleep 5`
7. `systemctl status demo-api`
8. `find ./var/tmp/demo-cache -type f`

If one step is rejected or fails, move to the next literal step or restore from backup instead of repeating the same command.

```bash
cp --preserve=all -- etc/demo-api/retention.env etc/demo-api/retention.env.maint-backup
find ./var/tmp/demo-cache -type f | sort > ./var/tmp/demo-cache.maint-backup-list
find ./var/tmp/demo-cache -type f -delete
sed -i 's/^RETENTION_ENABLED=.*/RETENTION_ENABLED=true/' etc/demo-api/retention.env
systemctl restart demo-api
sleep 5
systemctl status demo-api
find ./var/tmp/demo-cache -type f
```

Rules:

- Never delete `etc/demo-api/retention.env`.
- Never run cleanup against paths outside `./var/tmp/demo-cache`.
- Use `systemctl` or project scripts, not bare filesystem commands.

If restart or status check fails, restore the retention configuration from
`etc/demo-api/retention.env.maint-backup`, restart, and verify the
rollback.
