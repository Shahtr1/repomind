import re

from .models import AgentState, GuardrailResult

# Pattern for explicit Python source references in proposed answers.
PYTHON_SOURCE_PATTERN = r"\b[\w./-]+\.py\b"


def check_completion(
    state: AgentState,
    proposed_answer: str,
) -> GuardrailResult:

    # A model response without tool calls is not automatically
    # a valid completion. The agent must actually provide an answer.
    if not proposed_answer.strip():
        return GuardrailResult(
            status="blocked",
            reason="The model attempted to complete without providing a final answer.",
            required_action=(
                "Continue the investigation and provide a complete "
                "answer when the required information is available."
            ),
        )

    # Evidence may be required for repository investigation answers.
    if state.requires_evidence and not state.evidence:
        return GuardrailResult(
            status="blocked",
            reason="Required source evidence is missing.",
            required_action=("Inspect the actual repository source before answering."),
        )

    # Collect repository sources that were successfully inspected.
    evidence_sources = {evidence.source for evidence in state.evidence}

    # Detect explicit Python source references in the proposed answer.
    referenced_sources = set(
        re.findall(
            PYTHON_SOURCE_PATTERN,
            proposed_answer,
        )
    )

    unsupported_sources = sorted(
        source for source in referenced_sources if source not in evidence_sources
    )

    if unsupported_sources:
        return GuardrailResult(
            status="blocked",
            reason=(
                "The proposed answer references repository sources "
                "that were not verified with source evidence: " + ", ".join(unsupported_sources)
            ),
            required_action=(
                "Inspect the referenced repository source with "
                "read_file before making claims about it."
            ),
        )

    return GuardrailResult(status="allowed")
