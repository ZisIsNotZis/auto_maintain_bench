# Shell and Editing Reference

## Working Directory

Each bash command runs in a fresh shell session. The working directory is always `/sandbox/`.
- `cd` does NOT persist to the next command
- Use relative paths directly: `cat etc/service/config.env` resolves to `/sandbox/etc/service/config.env`
- For multi-step work in a subdirectory, chain with `&&`: `cd /sandbox/subdir && cat file.txt && ...`
- Better: just use the path directly — no need to cd at all

## sed Quoting Rules

### Single quotes (preferred)
- `sed -i 's/^KEY=.*/KEY=value/' etc/service/config.env` — single quotes prevent shell expansion
- Inside single quotes, everything is literal except another single quote

### Double quotes (use with caution)
- Only use double quotes when you need variable expansion
- If the pattern contains `$`, `` ` ``, or `!`, use single quotes

### Common sed patterns
- Replace entire line: `sed -i 's/^KEY=.*/KEY=new_value/' file`
- Replace a value in structured formats: `sed -i 's/^  key: .*/  key: new_value/' file.yaml`
- Replace specific value: `sed -i 's/old_value/new_value/' file`
- Delete a line: `sed -i '/^KEY=.*/d' file`
- Important: always read the file first with `cat` to see the exact current value before writing sed

### Common sed mistakes
- Forgetting `-i` — sed only prints to stdout without it
- Forgetting `^` anchor — matches anywhere in the line, not just at the start
- Unescaped special characters in the pattern (`.`, `*`, `[`, `]`, `\`, `/`, `&`)
- Using `/` in the pattern without escaping: `sed -i 's/\/path\/to\/file/\/new\/path/'` — use a different delimiter: `sed -i 's|/path/to/file|/new/path|'`
- Wrong quote type causing shell expansion of the pattern
- Not reading the file first — the current value might not be what you assume

## Heredoc Syntax

```
cat > etc/service/config.env << 'EOF'
KEY=value
OTHER_KEY=other_value
EOF
```

- The delimiter (EOF) must be on its own line at the start and end of the content
- Use `'EOF'` (quoted) to prevent shell expansion inside the heredoc
- Content goes BETWEEN the delimiters, not on the same line as `<<`
- The first `EOF` must follow `<< ` immediately (with a space)
- The closing `EOF` must be alone on its line with no leading/trailing whitespace

## Command Patterns

### Locating config files
- `ls -la etc/` / `ls -la config/` — check common config directories
- `find . -name "*.env" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" -o -name "*.conf" -o -name "*.json" -o -name "*.ini" -o -name "*.cfg"` — find config files anywhere
- `systemctl cat <service>` — read the service's unit file to find the startup command and config locations
- `find . -type f -name "*.env" -o -name "*.conf" | head -20` — limit results

### Reading files
- `cat etc/service/config.env` — view file contents
- `ls -la etc/service/` — list directory
- `head -50 etc/service/config.yaml` — read first 50 lines of a potentially large file

### Editing files
- `sed -i 's/^OLD_KEY=.*/OLD_KEY=new_value/' etc/service/config.env` — single line change (preferred)
- `cat > etc/service/config.env << 'EOF' ... EOF` — full file replacement (only when truly needed, and only after reading the original)

### Checking file after edit
- `cat etc/service/config.env` — verify your edit was applied correctly
- `grep 'KEY' etc/service/config.env` — check a specific key

### Restarting services
- `systemctl restart <service-name>` — use the name from telemetry, not a guess
- `systemctl status <service-name>` — check if the restart succeeded

### Verification
- `sleep 10` — wait for next telemetry tick
- `cat _harness/telemetry/latest.json` — check latest telemetry snapshot
- `cat _harness/telemetry/latest.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps({s['name']: {'state':s['state'],'health':s.get('health','?')} for s in d['services']}, indent=2))"` — quick service status check