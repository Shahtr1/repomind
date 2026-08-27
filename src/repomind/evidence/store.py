from ..models import (
    AgentState,
    Evidence,
    EvidenceConfig,
)


def add_evidence(
    state: AgentState,
    source: str,
    content: str,
) -> None:

    state.evidence.append(
        Evidence(
            source=source,
            content=content,
        )
    )


def resolve_evidence_source(
    evidence_config: EvidenceConfig,
    tool_arguments: dict,
) -> str:

    return evidence_config.source_resolver(tool_arguments)


def add_tool_evidence(
    state: AgentState,
    evidence_config: EvidenceConfig,
    tool_arguments: dict,
    result: str,
) -> None:

    source = resolve_evidence_source(
        evidence_config,
        tool_arguments,
    )

    add_evidence(
        state,
        source=source,
        content=result,
    )


def select_evidence(
    state: AgentState,
    selected_sources: set[str],
) -> list[Evidence]:

    # Evidence is only injected when its source is not already
    # represented by a selected conversation message.
    return [
        evidence
        for evidence in state.evidence
        if evidence.source not in selected_sources
    ]


def evidence_message(evidence: Evidence) -> dict:

    return {
        "role": "system",
        "content": (
            "Verified repository evidence\n\n"
            f"Source: {evidence.source}\n\n"
            f"{evidence.content}"
        ),
    }
