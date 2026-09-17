# RepoMind

RepoMind is a production-style repository investigation agent built in Python to explore how repository-aware AI agents work in practice. The project is designed to reason over source code, use repository tools intentionally, enforce policy and guardrails, and keep explicit evidence for each step.

## Goals

RepoMind focuses on the core architecture behind trustworthy repository investigation agents, including:

- Local LLM inference with Ollama
- Structured agent state and execution loops
- Tool discovery, validation, and execution
- Policy enforcement and approval flows
- Guardrails for completion decisions
- Evidence tracking and source attribution
- Context assembly and repository awareness
- Retrieval and document parsing
- Evaluation and observability

## Architecture

```text
User
 ↓
Agent
 ↓
Context Assembly
 ↓
LLM
 ↓
Decision
 ├── Final Answer
 └── Tool Call
       ↓
Policy
       ↓
Guardrail
       ↓
Approval?
       ↓
Execution
       ↓
Result
       ↓
Evidence / State / Events
       ↓
Agent continues
```

## What this project does

RepoMind implements a lightweight repository investigation workflow where:

- the model decides whether it needs repository information
- the application enforces tool policies and guardrails
- relevant source material is inspected before a claim is made
- completion is only allowed when the evidence is sufficient
- agent events, state, and evidence are retained across steps

This makes the agent behave more like an auditable investigation workflow than a free-form chat assistant.

## Local setup

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Run the agent:

```bash
python -m repomind.main
```

Run tests:

```bash
pytest -q
```

## Repository structure

```text
repomind/
├── README.md
├── pyproject.toml
├── src/
│   └── repomind/
│       ├── __init__.py
│       ├── agent.py
│       ├── answers/
│       │   ├── __init__.py
│       │   └── reconstruction.py
│       ├── config.py
│       ├── context.py
│       ├── context/
│       │   ├── __init__.py
│       │   ├── builder.py
│       │   ├── dependencies.py
│       │   └── selection.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── constants.py
│       │   └── models.py
│       ├── display.py
│       ├── evidence/
│       │   ├── __init__.py
│       │   └── store.py
│       ├── executor.py
│       ├── guardrails.py
│       ├── llm.py
│       ├── main.py
│       ├── orchestration/
│       │   ├── __init__.py
│       │   ├── approvals.py
│       │   ├── decisions.py
│       │   ├── execution_results.py
│       │   ├── persistence.py
│       │   ├── responses.py
│       │   ├── runner.py
│       │   ├── state_machine.py
│       │   └── tool_calls.py
│       ├── policy.py
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── event_messages.py
│       │   ├── recovery.py
│       │   └── tool_messages.py
│       ├── registry.py
│       ├── retrieval/
│       │   ├── __init__.py
│       │   └── parser.py
│       ├── state.py
│       ├── tool_results.py
│       └── tools.py
├── tests/
│   └── test_guardrails.py
└── .gitignore
```

## Notes

- `src/repomind/` contains the implementation of the agent, orchestration flow, LLM integration, context assembly, policy checks, and execution logic.
- `src/repomind/orchestration/` holds the request lifecycle pieces such as approvals, runner flow, decision handling, and state transitions.
- `src/repomind/prompts/` stores the prompt templates and message definitions used during execution and recovery flows.
- `src/repomind/data/` contains shared constants and models used by the agent.
- `tests/` holds the project’s validation coverage, currently centered on guardrail behavior.
