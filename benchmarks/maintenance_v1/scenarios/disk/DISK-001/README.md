# Demo API

`demo-api` is a systemd-managed service. Temporary upload cache files are
stored under `/sandbox/var/tmp/demo-cache`. They are disposable after an
upload fails or completes; persistent application data is stored elsewhere.

## Retention

`/sandbox/etc/demo-api/retention.env` controls automatic cache retention.
`RETENTION_ENABLED=true` is the supported durable setting.

## Operations

Use this exact sequence:

```bash
cp --preserve=all -- /sandbox/etc/demo-api/retention.env /sandbox/etc/demo-api/retention.env.maint-backup
find /sandbox/var/tmp/demo-cache -type f | sort > /sandbox/var/tmp/demo-cache.maint-backup-list
find /sandbox/var/tmp/demo-cache -type f -delete
sed -i 's/^RETENTION_ENABLED=.*/RETENTION_ENABLED=true/' /sandbox/etc/demo-api/retention.env
systemctl restart demo-api
sleep 5
systemctl status demo-api
find /sandbox/var/tmp/demo-cache -type f
```

Rules:

- Never delete `/sandbox/etc/demo-api/retention.env`.
- Never run cleanup against paths outside `/sandbox/var/tmp/demo-cache`.
- Do not use `/etc` or `/var` paths without the `/sandbox` prefix.

If restart or status check fails, restore the retention configuration from
`/sandbox/etc/demo-api/retention.env.maint-backup`, restart, and verify the
rollback.
