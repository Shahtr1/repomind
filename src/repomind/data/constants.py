from enum import StrEnum


class ToolExecutionStatus(StrEnum):
    SUCCESS = "success"
    DENIED = "denied"
    APPROVAL_REQUIRED = "approval_required"
    INVALID_ARGUMENTS = "invalid_arguments"
    ERROR = "error"


class AgentStatus(StrEnum):
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class GuardrailStatus(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


class AgentEventType(StrEnum):
    GUARDRAIL_BLOCKED = "guardrail_blocked"
    GENERATION_TRUNCATED = "generation_truncated"
    INVESTIGATION_CONTINUED = "investigation_continued"
    INVESTIGATION_CANNOT_COMPLETE = "investigation_cannot_complete"


class LLMDecisionType(StrEnum):
    PROPOSE_FINAL_ANSWER = "propose_final_answer"
    CANNOT_COMPLETE = "cannot_complete"


class LLMFinishReason(StrEnum):
    STOP = "stop"
    LENGTH = "length"
    UNKNOWN = "unknown"


class LLMPhase(StrEnum):
    TOOL_USE = "tool_use"
    COMPLETION_DECISION = "completion_decision"
    FINAL_ANSWER = "final_answer"
