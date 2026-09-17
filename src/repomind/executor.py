from data.models import ToolExecutionResult, ToolOutcome

from .policy import tool_policy
from .registry import tool_registry

# --------------------------------------------------
# Tool execution
# --------------------------------------------------


def execute_tool(
    tool_name: str, tool_arguments: dict, approved: bool = False
) -> ToolExecutionResult:

    # Tool existence

    if tool_name not in tool_registry:
        return ToolExecutionResult(status="error", error=f"Unknown tool: {tool_name}")

    # Policy

    policy = tool_policy.get(tool_name)

    if policy is None or not policy.allowed:
        return ToolExecutionResult(
            status="denied",
            error=f"Tool '{tool_name}' is denied by application policy.",
        )

    # Approval

    if policy.requires_approval and not approved:
        return ToolExecutionResult(
            status="approval_required",
            error=f"Human approval is required before executing '{tool_name}'.",
        )

    # Registry

    tool_definition = tool_registry[tool_name]

    tool = tool_definition.function
    argument_schema = tool_definition.arguments

    # Argument validation

    try:
        arguments = argument_schema.model_validate(tool_arguments)

    except Exception as error:
        return ToolExecutionResult(status="invalid_arguments", error=str(error))

    # Execution

    try:
        outcome = tool(**arguments.model_dump())

        if not isinstance(outcome, ToolOutcome):
            return ToolExecutionResult(
                status="error",
                error=(
                    f"Tool '{tool_name}' returned an invalid outcome type: {type(outcome).__name__}"
                ),
            )

        if not outcome.success:
            return ToolExecutionResult(
                status="error",
                error=outcome.error,
            )

        return ToolExecutionResult(
            status="success",
            result=outcome.result,
        )

    except Exception as error:
        return ToolExecutionResult(status="error", error=str(error))
