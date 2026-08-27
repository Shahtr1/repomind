def print_tool_result(execution) -> None:

    print("\nTool execution result:")

    print(
        f"Status: {execution.status}"
    )

    if execution.result is not None:

        print("\nResult:")
        print(execution.result)

    if execution.error is not None:

        print("\nError:")
        print(execution.error)