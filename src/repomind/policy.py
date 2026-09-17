from data.models import ToolPolicy

tool_policy: dict[str, ToolPolicy] = {
    "read_file": ToolPolicy(
        allowed=True,
        requires_approval=False,
    ),
    "list_files": ToolPolicy(
        allowed=True,
        requires_approval=False,
    ),
    "create_note": ToolPolicy(
        allowed=True,
        requires_approval=True,
    ),
    "search_files": ToolPolicy(
        allowed=True,
        requires_approval=False,
    ),
}
