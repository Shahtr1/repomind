import re
from enum import StrEnum

from data.models import AgentState, GuardrailResult
from pydantic import BaseModel


class SourceReferenceResolutionStatus(StrEnum):
    """
    Describes how a source reference in a proposed answer resolves
    against the repository sources represented by collected evidence.
    """

    SUPPORTED = "supported"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"


class SourceReferenceResolution(BaseModel):
    """
    Represents the result of resolving a source reference from a proposed
    answer against the repository sources represented by collected evidence.
    """

    status: SourceReferenceResolutionStatus
    referenced_source: str
    matching_sources: list[str]


def normalize_source_path(
    source: str,
) -> str:
    """
    Normalize repository source paths for comparison.
    """

    return source.replace("\\", "/")


def source_basename(
    source: str,
) -> str:
    """
    Return the filename portion of a repository source reference.
    """

    normalized_source = normalize_source_path(source)

    return normalized_source.rsplit("/", maxsplit=1)[-1]


def resolve_source_reference(
    referenced_source: str,
    evidence_sources: set[str],
) -> SourceReferenceResolution:
    """
    Resolve a source reference from a proposed answer against evidence sources.

    Resolution rules:

    1. Normalized exact path match -> supported.
    2. Exactly one matching basename -> supported.
    3. Multiple matching basenames -> ambiguous.
    4. No match -> unsupported.
    """

    normalized_referenced_source = normalize_source_path(
        referenced_source,
    )

    exact_matches = [
        evidence_source
        for evidence_source in evidence_sources
        if normalize_source_path(evidence_source) == normalized_referenced_source
    ]

    if exact_matches:
        return SourceReferenceResolution(
            status=SourceReferenceResolutionStatus.SUPPORTED,
            referenced_source=referenced_source,
            matching_sources=exact_matches,
        )

    referenced_basename = source_basename(
        referenced_source,
    )

    matching_sources = sorted(
        evidence_source
        for evidence_source in evidence_sources
        if source_basename(evidence_source) == referenced_basename
    )

    if len(matching_sources) == 1:
        return SourceReferenceResolution(
            status=SourceReferenceResolutionStatus.SUPPORTED,
            referenced_source=referenced_source,
            matching_sources=matching_sources,
        )

    if len(matching_sources) > 1:
        return SourceReferenceResolution(
            status=SourceReferenceResolutionStatus.AMBIGUOUS,
            referenced_source=referenced_source,
            matching_sources=matching_sources,
        )

    return SourceReferenceResolution(
        status=SourceReferenceResolutionStatus.UNSUPPORTED,
        referenced_source=referenced_source,
        matching_sources=[],
    )


PYTHON_SOURCE_PATTERN = r"\b[\w./-]+\.py\b"


def check_completion(
    state: AgentState,
    proposed_answer: str,
) -> GuardrailResult:

    result = check_answer_content(proposed_answer)

    if result is not None:
        return result

    result = check_evidence_requirement(state)

    if result is not None:
        return result

    result = check_source_references(
        state,
        proposed_answer,
    )

    if result is not None:
        return result

    return GuardrailResult(status="allowed")


def check_answer_content(
    proposed_answer: str,
) -> GuardrailResult | None:

    if proposed_answer.strip():
        return None

    return GuardrailResult(
        status="blocked",
        reason="The model attempted to complete without providing a final answer.",
        required_action=(
            "Continue the investigation and provide a complete "
            "answer when the required information is available."
        ),
    )


def check_evidence_requirement(
    state: AgentState,
) -> GuardrailResult | None:

    if not state.requires_evidence:
        return None

    if state.evidence:
        return None

    return GuardrailResult(
        status="blocked",
        reason="Required source evidence is missing.",
        required_action="Inspect the actual repository source before answering.",
    )


def check_source_references(
    state: AgentState,
    proposed_answer: str,
) -> GuardrailResult | None:

    evidence_sources = {evidence.source for evidence in state.evidence}

    referenced_sources = set(
        re.findall(
            PYTHON_SOURCE_PATTERN,
            proposed_answer,
        )
    )

    unsupported_sources: list[str] = []
    ambiguous_sources: list[str] = []

    for referenced_source in referenced_sources:
        resolution = resolve_source_reference(
            referenced_source,
            evidence_sources,
        )

        if resolution.status == SourceReferenceResolutionStatus.UNSUPPORTED:
            unsupported_sources.append(referenced_source)

        elif resolution.status == SourceReferenceResolutionStatus.AMBIGUOUS:
            ambiguous_sources.append(referenced_source)

    if not unsupported_sources and not ambiguous_sources:
        return None

    problems: list[str] = []

    if unsupported_sources:
        problems.append("Unsupported source references: " + ", ".join(sorted(unsupported_sources)))

    if ambiguous_sources:
        problems.append("Ambiguous source references: " + ", ".join(sorted(ambiguous_sources)))

    return GuardrailResult(
        status="blocked",
        reason=(
            "The proposed answer contains source references that "
            "cannot be safely verified against collected evidence. " + " ".join(problems)
        ),
        required_action=(
            "Inspect the referenced repository source with read_file "
            "and use an unambiguous source reference before making "
            "claims about it."
        ),
    )
