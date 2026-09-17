from repomind.data.models import ToolExecutionResult


def print_tool_result(
    execution: ToolExecutionResult,
) -> None:
    print(f"\nTool execution result: {execution.status}")

    if execution.error is not None:
        print(f"Error: {execution.error}")
