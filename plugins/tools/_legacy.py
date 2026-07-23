from harness.tools import execute_tool


def handler(tool):
    def handle(*, args, state, scenario):
        return execute_tool(tool=tool, args=args, state=state, scenario=scenario)

    return handle
