from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from .event_feed import WorldState
from .scenario_schema import Scenario
from .tools import ToolResult


class ToolRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root

    def union_schema(self, names: list[str]) -> dict[str, Any]:
        return {"oneOf": [self._schema(name) for name in names]}

    def invoke(
        self,
        call: dict[str, Any],
        *,
        state: WorldState,
        scenario: Scenario,
    ) -> ToolResult:
        name = str(call.get("type", "")).strip()
        if not name or not self._schema_path(name).is_file():
            raise ValueError(f"unknown tool: {name or '<empty>'}")
        schema = self._schema(name)
        expected = schema.get("properties", {}).get("type", {}).get("const")
        if expected != name:
            raise ValueError(f"tool discriminator mismatch: {name}")
        errors = _validate(call, schema)
        if errors:
            raise ValueError(f"invalid tool call {name}: {'; '.join(errors)}")
        args = call["args"]
        handler = self._load_handler(name)
        return handler(args=args, state=state, scenario=scenario)

    def _schema(self, name: str) -> dict[str, Any]:
        path = self._schema_path(name)
        if not path.is_file():
            raise ValueError(f"unknown tool: {name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _schema_path(self, name: str) -> Path:
        return self.root / f"{name}.schema.json"

    def _load_handler(self, name: str) -> Any:
        path = self.root / f"{name}.py"
        if not path.is_file():
            raise ValueError(f"missing tool handler: {name}")
        spec = importlib.util.spec_from_file_location(f"maintenance_tool_{name}", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"cannot load tool handler: {name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = getattr(module, "handle", None)
        if not callable(handler):
            raise ValueError(f"tool handler has no handle function: {name}")
        return handler


def _validate(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            return [f"{path} must be object"]
        errors: list[str] = []
        required = schema.get("required", [])
        errors.extend(f"{path}.{key} is required" for key in required if key not in value)
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            errors.extend(f"{path}.{key} is not allowed" for key in value if key not in properties)
        for key, child_schema in properties.items():
            if key in value and isinstance(child_schema, dict):
                errors.extend(_validate(value[key], child_schema, f"{path}.{key}"))
        return errors
    if expected_type == "array":
        if not isinstance(value, list):
            return [f"{path} must be array"]
        item_schema = schema.get("items", {})
        return [
            error
            for index, item in enumerate(value)
            for error in _validate(item, item_schema, f"{path}[{index}]")
        ]
    if expected_type == "string":
        if not isinstance(value, str):
            return [f"{path} must be string"]
        if len(value) < int(schema.get("minLength", 0)):
            return [f"{path} is too short"]
    if expected_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return [f"{path} must be integer"]
        if "minimum" in schema and value < int(schema["minimum"]):
            return [f"{path} is below minimum"]
    if "const" in schema and value != schema["const"]:
        return [f"{path} must equal {schema['const']!r}"]
    return []
