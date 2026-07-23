from harness.tools import execute_tool


def handle(*, args, state, scenario):
    return execute_tool(tool="inspect_metrics", args=args, state=state, scenario=scenario)
