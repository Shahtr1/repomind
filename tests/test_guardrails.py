import pytest

from repomind.guardrails import (
    SourceReferenceResolutionStatus,
    check_answer_content,
    check_completion,
    check_evidence_requirement,
    check_source_references,
    normalize_source_path,
    resolve_evidence_source,
    source_basename,
)
from repomind.models import AgentState, Evidence


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("src\\repomind\\guardrails.py", "src/repomind/guardrails.py"),
        ("src/repomind/guardrails.py", "src/repomind/guardrails.py"),
        ("src\\nested\\file.py", "src/nested/file.py"),
    ],
)
def test_normalize_source_path_replaces_windows_separators(
    source: str,
    expected: str,
) -> None:
    assert normalize_source_path(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("src\\repomind\\guardrails.py", "guardrails.py"),
        ("src/repomind/guardrails.py", "guardrails.py"),
        ("src/nested/file.py", "file.py"),
    ],
)
def test_source_basename_extracts_filename(source: str, expected: str) -> None:
    assert source_basename(source) == expected


@pytest.mark.parametrize(
    ("referenced_source", "evidence_sources", "expected_status", "expected_matches"),
    [
        (
            "src/repomind/guardrails.py",
            {"src/repomind/guardrails.py"},
            SourceReferenceResolutionStatus.SUPPORTED,
            ["src/repomind/guardrails.py"],
        ),
        (
            "src\\repomind\\guardrails.py",
            {"src/repomind/guardrails.py"},
            SourceReferenceResolutionStatus.SUPPORTED,
            ["src/repomind/guardrails.py"],
        ),
        (
            "config.py",
            {"src/alpha/config.py", "src/beta/config.py"},
            SourceReferenceResolutionStatus.AMBIGUOUS,
            ["src/alpha/config.py", "src/beta/config.py"],
        ),
        (
            "config.py",
            {"src/alpha/other.py"},
            SourceReferenceResolutionStatus.UNSUPPORTED,
            [],
        ),
    ],
)
def test_resolve_evidence_source_handles_core_edge_cases(
    referenced_source: str,
    evidence_sources: set[str],
    expected_status: SourceReferenceResolutionStatus,
    expected_matches: list[str],
) -> None:
    resolution = resolve_evidence_source(referenced_source, evidence_sources)

    assert resolution.status == expected_status
    assert resolution.referenced_source == referenced_source
    assert resolution.matching_sources == expected_matches


def test_resolve_evidence_source_prefers_exact_path_over_basename_match() -> None:
    evidence_sources = {
        "src/alpha/worker.py",
        "src/beta/worker.py",
    }

    resolution = resolve_evidence_source("src/beta/worker.py", evidence_sources)

    assert resolution.status == SourceReferenceResolutionStatus.SUPPORTED
    assert resolution.matching_sources == ["src/beta/worker.py"]


@pytest.mark.parametrize(
    ("proposed_answer", "expected"),
    [
        ("", "blocked"),
        ("   \n\t  ", "blocked"),
        ("The answer is ready.", None),
    ],
)
def test_check_answer_content_blocks_empty_answers(
    proposed_answer: str,
    expected: str | None,
) -> None:
    result = check_answer_content(proposed_answer)

    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result.status == expected


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (AgentState(messages=[], requires_evidence=True, evidence=[]), "blocked"),
        (AgentState(messages=[], requires_evidence=False, evidence=[]), None),
        (
            AgentState(
                messages=[],
                requires_evidence=True,
                evidence=[Evidence(source="src/repomind/guardrails.py", content="x")],
            ),
            None,
        ),
    ],
)
def test_check_evidence_requirement_handles_missing_and_present_evidence(
    state: AgentState,
    expected: str | None,
) -> None:
    result = check_evidence_requirement(state)

    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result.status == expected


def test_check_source_references_blocks_unsupported_and_ambiguous_references() -> None:
    state = AgentState(
        messages=[],
        evidence=[
            Evidence(source="src/alpha/service.py", content="alpha"),
            Evidence(source="src/beta/service.py", content="beta"),
        ],
    )

    result = check_source_references(
        state,
        "See service.py and src/alpha/service.py and missing.py.",
    )

    assert result is not None
    assert result.status == "blocked"
    assert "Ambiguous source references: service.py" in result.reason
    assert "Unsupported source references: missing.py" in result.reason


def test_check_completion_allows_valid_submission() -> None:
    state = AgentState(
        messages=[],
        requires_evidence=True,
        evidence=[Evidence(source="src/repomind/guardrails.py", content="content")],
    )

    result = check_completion(
        state,
        "This is supported by src/repomind/guardrails.py.",
    )

    assert result.status == "allowed"


def test_check_completion_blocks_empty_answer_before_other_checks() -> None:
    state = AgentState(
        messages=[],
        requires_evidence=True,
        evidence=[],
    )

    result = check_completion(state, "   ")

    assert result.status == "blocked"
    assert result.reason == (
        "The model attempted to complete without providing a final answer."
    )
