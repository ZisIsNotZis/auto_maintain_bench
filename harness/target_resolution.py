from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedTarget:
    kind: str
    model: str
    base_url: str | None
    local_model: bool


def resolve_target(
    *,
    model: str,
    base_url: str | None,
) -> ResolvedTarget:
    if not model:
        raise ValueError("model is required")
    local_model = model.startswith("./")
    if not local_model and not base_url:
        raise ValueError("named raw model requires --base-url")
    return ResolvedTarget(
        kind="raw",
        model=model,
        base_url=base_url,
        local_model=local_model,
    )
