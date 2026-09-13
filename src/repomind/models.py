from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field, StrictStr

from .config import MAX_STEPS

ToolExecutionStatus = Literal[
    "success", "denied", "approval_required", "invalid_arguments", "error"
]


class ToolOutcome(BaseModel):
    """
    Represents the outcome of the underlying tool operation.

    This is different from ToolExecutionResult, which represents the
    executor's higher-level result after policy, approval, argument
    validation, and tool execution have been handled.
    """

    success: bool
    result: str | None = None
    error: str | None = None


class ToolExecutionResult(BaseModel):
    status: ToolExecutionStatus
    result: str | None = None
    error: str | None = None


AgentStatus = Literal["running", "waiting_for_approval", "completed", "failed"]


class PendingToolCall(BaseModel):
    tool_call_id: str
    tool_name: str
    arguments: dict


class ToolPolicy(BaseModel):
    allowed: bool
    requires_approval: bool


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


LLMFinishReason = Literal[
    "stop",
    "length",
    "unknown",
]


class LLMToolCall(BaseModel):
    id: str
    name: str
    arguments: dict


class LLMResponse(BaseModel):
    content: str
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    finish_reason: LLMFinishReason


class Message(BaseModel):
    id: str
    sequence: int
    payload: dict  # LLM/Ollama data
    source: str | None = None  # provenance
    persistent: bool = False  # context-retention policy


class AgentEvent(BaseModel):
    type: Literal["guardrail_blocked", "generation_truncated"]
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

    # Each agent state receives its own independent evidence collection.
    evidence: list[Evidence] = Field(default_factory=list)

    events: list[AgentEvent] = Field(default_factory=list)
