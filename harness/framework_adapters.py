from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameworkAdapterSpec:
    name: str
    harness_profile: str
    prompt_style: str
    tool_mode: str
    memory_mode: str
    recovery_mode: str
    description: str
    command_hint: str


FRAMEWORK_ADAPTERS: dict[str, FrameworkAdapterSpec] = {
    "generic_conversation": FrameworkAdapterSpec(
        name="generic_conversation",
        harness_profile="llama_cpp_agent_style",
        prompt_style="strict_json",
        tool_mode="retrieval",
        memory_mode="rolling",
        recovery_mode="heuristic",
        description="Framework-independent conversation adapter over OpenAI-compatible llama-server.",
        command_hint="python3 run.py --agent-mode llama_json --adapter generic_conversation ...",
    ),
    "llama_cpp_agent": FrameworkAdapterSpec(
        name="llama_cpp_agent",
        harness_profile="llama_cpp_agent_style",
        prompt_style="strict_json",
        tool_mode="retrieval",
        memory_mode="rolling",
        recovery_mode="heuristic",
        description="llama-cpp-agent style: strict schema, small tool set, deterministic recovery.",
        command_hint="Future native adapter should bind llama-cpp-agent tools/GBNF; current adapter emulates its prompt/tool policy.",
    ),
    "smolagents": FrameworkAdapterSpec(
        name="smolagents",
        harness_profile="smolagents_style",
        prompt_style="ops_playbook",
        tool_mode="all",
        memory_mode="none",
        recovery_mode="heuristic",
        description="smolagents style: practical SRE playbook prompt with direct tool action.",
        command_hint="Future native adapter should wrap smolagents ToolCallingAgent; current adapter emulates its conversation/tool policy.",
    ),
    "tinyagent": FrameworkAdapterSpec(
        name="tinyagent",
        harness_profile="tinyagent_style",
        prompt_style="minimal",
        tool_mode="retrieval",
        memory_mode="rolling",
        recovery_mode="heuristic",
        description="TinyAgent style: short prompt, retrieved tools only, rolling compact memory.",
        command_hint="Future native adapter should call TinyAgent runtime; current adapter emulates its compact tool-retrieval policy.",
    ),
    "pure_llama_json": FrameworkAdapterSpec(
        name="pure_llama_json",
        harness_profile="llama_cpp_agent_style",
        prompt_style="strict_json",
        tool_mode="retrieval",
        memory_mode="rolling",
        recovery_mode="none",
        description="Control adapter: raw llama-server JSON output without deterministic recovery.",
        command_hint="python3 run.py --agent-mode llama_json --adapter pure_llama_json ...",
    ),
}


def get_adapter(name: str) -> FrameworkAdapterSpec:
    try:
        return FRAMEWORK_ADAPTERS[name]
    except KeyError as exc:
        allowed = ", ".join(sorted(FRAMEWORK_ADAPTERS))
        raise ValueError(f"unknown adapter {name!r}; allowed: {allowed}") from exc

