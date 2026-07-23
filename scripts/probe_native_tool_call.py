#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib import request


BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Execute one shell command.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "required": ["command"],
            "properties": {
                "command": {
                    "type": "string",
                }
            },
        },
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18091/v1")
    parser.add_argument("--model", default="qwen")
    parser.add_argument("--system", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--expect-command")
    parser.add_argument("--reject-prefix")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    system_path = Path(args.system)
    system = (
        system_path.read_text(encoding="utf-8").strip()
        if system_path.is_file()
        else args.system
    )
    failures = 0
    for attempt in range(1, args.repeat + 1):
        payload = _complete(
            base_url=args.base_url,
            model=args.model,
            system=system,
            user=args.user,
        )
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        calls = message.get("tool_calls") or []
        command = None
        if len(calls) == 1:
            function = calls[0].get("function") or {}
            arguments = function.get("arguments", "{}")
            parsed = json.loads(arguments) if isinstance(arguments, str) else arguments
            if function.get("name") == "bash" and isinstance(parsed, dict):
                command = parsed.get("command")
        ok = (
            command == args.expect_command
            if args.expect_command is not None
            else isinstance(command, str)
        )
        if args.reject_prefix and isinstance(command, str):
            ok = ok and not command.startswith(args.reject_prefix)
        failures += int(not ok)
        print(
            json.dumps(
                {
                    "attempt": attempt,
                    "ok": ok,
                    "content": message.get("content"),
                    "reasoning_content": message.get("reasoning_content"),
                    "tool_calls": calls,
                    "parsed_command": command,
                },
                ensure_ascii=True,
            )
        )
    if failures:
        raise SystemExit(1)


def _complete(
    *,
    base_url: str,
    model: str,
    system: str,
    user: str,
) -> dict[str, object]:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "tools": [BASH_TOOL],
        "tool_choice": "required",
        "temperature": 0,
        "max_tokens": 128,
    }
    req = request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        method="POST",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()
