# Demo API

`demo-api` is a systemd-managed service configured by
`/sandbox/etc/demo-api/config.yaml`.

## Configuration

The minimal valid worker configuration is:

```yaml
workers: 2
```

The service must not be restarted repeatedly while the YAML is malformed.

## Operations

Use this exact sequence:

```bash
cp --preserve=all -- /sandbox/etc/demo-api/config.yaml /sandbox/etc/demo-api/config.yaml.maint-backup
cat > /sandbox/etc/demo-api/config.yaml << 'EOF'
workers: 2
EOF
systemctl restart demo-api
sleep 5
systemctl status demo-api
cat /sandbox/etc/demo-api/config.yaml
```

Rules:

- Keep the file as exactly one line: `workers: 2`.
- Do not use awk/sed rewrites for this case; overwrite with the exact heredoc
  above.
- Do not use `/etc` paths without the `/sandbox` prefix.

If restart or status check fails, restore the backup, restart, and verify the
rollback before escalating.
