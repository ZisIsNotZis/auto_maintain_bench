from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .baseline_agent import BaselineRuleAgent
from .llm_agent import LlamaJSONAgent


@dataclass(frozen=True)
class VisibleMessage:
    role: Literal["user", "assistant", "tool"]
    content: str


@dataclass(frozen=True)
class VisibleOutputProjection:
    visible_outputs: tuple[VisibleMessage, ...]
    final_output: str


@dataclass(frozen=True)
class ModelTarget:
    kind: Literal["baseline", "raw"]
    model: str | None = None
    base_url: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


def create_model_under_test(target: ModelTarget) -> Any:
    if target.kind == "baseline":
        return BaselineRuleAgent()
    if target.kind == "raw":
        if not target.base_url or not target.model:
            raise ValueError("raw model target requires base_url and model")
        return LlamaJSONAgent(
            base_url=target.base_url,
            model=target.model,
            **target.options,
        )
    raise ValueError(f"unsupported model target kind: {target.kind}")


def project_visible_output(events: list[dict[str, Any]]) -> VisibleOutputProjection:
    outputs: list[VisibleMessage] = []
    for event in events:
        if event.get("type") != "assistant.message":
            continue
        content = str(event.get("content", "") or "")
        if content:
            outputs.append(VisibleMessage(role="assistant", content=content))
    return VisibleOutputProjection(
        visible_outputs=tuple(outputs),
        final_output=outputs[-1].content if outputs else "",
    )
