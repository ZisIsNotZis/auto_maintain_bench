from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re


@dataclass(frozen=True)
class RejectionRule:
    name: str
    pattern: re.Pattern[str]
    stderr: str
    user_message: str


def load_rejection_rules(root: Path) -> tuple[RejectionRule, ...]:
    if not root.is_dir():
        return ()
    rules: list[RejectionRule] = []
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        pattern = re.compile(str(payload["pattern"]))
        rules.append(
            RejectionRule(
                name=str(payload["name"]),
                pattern=pattern,
                stderr=str(payload["stderr"]),
                user_message=str(payload["user_message"]),
            )
        )
    return tuple(rules)


def match_rejection(command: str, rules: tuple[RejectionRule, ...]) -> RejectionRule | None:
    for rule in rules:
        if rule.pattern.search(command):
            return rule
    return None
