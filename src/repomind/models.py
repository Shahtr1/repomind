from collections.abc import Callable
from typing import Any, Literal

from config import MAX_STEPS
from pydantic import BaseModel, Field, StrictStr

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


LLMDecisionType = Literal[
    "propose_final_answer",
    "cannot_complete",
]

LLMFinishReason = Literal[
    "stop",
    "length",
    "unknown",
]


class LLMToolCall(BaseModel):
    id: str
    name: str
    arguments: dict


class LLMDecision(BaseModel):
    """
    Represents the LLM's proposed completion decision.

    This model is used only when the model is not requesting a tool.

    The model does not describe the next investigation action here.
    If more repository information is required, it must request a
    native tool call instead.
    """

    decision: LLMDecisionType

    # Required when decision == "propose_final_answer".
    answer: str | None = None

    # Explains why the model selected the decision.
    reason: StrictStr


class LLMResponse(BaseModel):
    """
    Normalized response returned by the LLM adapter.

    The finish reason describes how generation ended.
    The decision describes what the model proposes to do next.

    These are different concepts:

        finish_reason == "stop"
            means only that model generation stopped.

        decision == "propose_final_answer"
            means the model proposed an answer, which still requires
            application-side completion validation.
    """

    content: str
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    finish_reason: LLMFinishReason
    decision: LLMDecision | None = None


class Message(BaseModel):
    id: str
    sequence: int
    payload: dict  # LLM/Ollama data
    source: str | None = None  # provenance
    persistent: bool = False  # context-retention policy


class AgentEvent(BaseModel):
    type: Literal[
        "guardrail_blocked",
        "generation_truncated",
        "investigation_continued",
        "investigation_cannot_complete",
    ]
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
