from repomind.data.models import (
    CreateNoteArguments,
    EvidenceConfig,
    ListFilesArguments,
    ReadFileArguments,
    SearchConfig,
    SearchFilesArguments,
    ToolDefinition,
)

from .retrieval.parser import parse_search_results
from .tools import create_note, list_files, read_file, search_files

read_file_tool = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Reads the complete contents of a repository file. "
            "Use this to INSPECT and VERIFY actual source code. "
            "This is the primary tool for obtaining source evidence."
        ),
        "parameters": ReadFileArguments.model_json_schema(),
    },
}


list_files_tool = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": (
            "Lists files in the repository. "
            "Use this only to discover file names. "
            "It does NOT inspect source code and does NOT provide "
            "evidence for answering implementation questions."
        ),
        "parameters": ListFilesArguments.model_json_schema(),
    },
}


create_note_tool = {
    "type": "function",
    "function": {
        "name": "create_note",
        "description": ("Creates a text file named agent_note.txt with the supplied content."),
        "parameters": CreateNoteArguments.model_json_schema(),
    },
}

search_files_tool = {
    "type": "function",
    "function": {
        "name": "search_files",
        "description": (
            "Searches repository text files for a query and returns "
            "matching file paths and lines. "
            "Use this to LOCATE relevant source code. "
            "Search results are not source evidence. "
        ),
        "parameters": SearchFilesArguments.model_json_schema(),
    },
}


tools = [read_file_tool, list_files_tool, create_note_tool, search_files_tool]

read_file_evidence = EvidenceConfig(source_resolver=lambda arguments: arguments["path"])

search_config = SearchConfig(result_parser=parse_search_results)

tool_registry: dict[str, ToolDefinition] = {
    "read_file": ToolDefinition(
        function=read_file, arguments=ReadFileArguments, evidence=read_file_evidence
    ),
    "list_files": ToolDefinition(function=list_files, arguments=ListFilesArguments),
    "create_note": ToolDefinition(function=create_note, arguments=CreateNoteArguments),
    "search_files": ToolDefinition(
        function=search_files, arguments=SearchFilesArguments, search=search_config
    ),
}
