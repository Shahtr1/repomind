from typing import Literal, Callable, Any

from pydantic import BaseModel, StrictStr, Field

from .config import MAX_STEPS

ToolExecutionStatus = Literal[
    "success", "denied", "approval_required", "invalid_arguments", "error"
]


class ToolExecutionResult(BaseModel):
    status: ToolExecutionStatus
    result: str | None = None
    error: str | None = None


AgentStatus = Literal["running", "waiting_for_approval", "completed", "failed"]


class PendingToolCall(BaseModel):
    tool_call_id: str
    tool_name: str
    arguments: dict


class Evidence(BaseModel):
    source: str
    content: str


class ReadFileArguments(BaseModel):
    path: StrictStr


class ListFilesArguments(BaseModel):
    pass


class CreateNoteArguments(BaseModel):
    content: StrictStr


class SearchFilesArguments(BaseModel):
    query: StrictStr


EvidenceSourceResolver = Callable[[dict], str]


class EvidenceConfig:
    def __init__(self, source_resolver: EvidenceSourceResolver):
        self.source_resolver = source_resolver


class SearchMatch(BaseModel):
    path: str
    line_number: int
    content: str


class SearchResult(BaseModel):
    query: str
    matches: list[SearchMatch]


SearchResultParser = Callable[[str, str], SearchResult]


class SearchConfig:
    def __init__(self, result_parser: SearchResultParser):
        self.result_parser = result_parser


GuardrailStatus = Literal["allowed", "blocked"]


class GuardrailResult(BaseModel):
    status: GuardrailStatus
    reason: str | None = None
    required_action: str | None = None


class ToolDefinition:
    def __init__(
        self,
        function: Callable[..., Any],
        arguments: type[BaseModel],
        evidence: EvidenceConfig | None = None,
        search: SearchConfig | None = None,
    ):
        self.function = function
        self.arguments = arguments
        self.evidence = evidence
        self.search = search


class Message(BaseModel):
    id: str
    sequence: int
    payload: dict  # LLM/Ollama data
    source: str | None = None  # provenance
    persistent: bool = False  # context-retention policy


class AgentEvent(BaseModel):
    type: Literal["guardrail_blocked"]
    step: int  # which agent iteration produced the event
    sequence: int  # exact position in the execution timeline
    reason: str | None = None
    required_action: str | None = None


class AgentState(BaseModel):
    messages: list[Message]
    step: int = 0
    sequence: int = 0
    max_steps: int = MAX_STEPS
    status: AgentStatus = "running"
    pending_tool_call: PendingToolCall | None = None

    requires_evidence: bool = True

    retrieval_results: list[SearchResult] = Field(default_factory=list)

    # Every time a new AgentState is created, call list() to create a brand-new empty list.

    # list is itself a callable.
    # When Pydantic needs a default:

    # list()

    # is called.

    # Imagine having two states, the two states must have independent evidence collections.
    evidence: list[Evidence] = Field(default_factory=list)

    events: list[AgentEvent] = Field(default_factory=list)
