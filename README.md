# RepoMind

RepoMind is a production-style repository investigation agent built from first principles.

## Goals

RepoMind is being built to explore and understand production AI agent architecture, including:

- Local LLM inference with Ollama
- Agent state and execution loops
- Tool calling and validation
- Tool policies
- Human approval workflows
- Guardrails
- Evidence
- Context engineering
- Repository-aware investigation
- Retrieval and RAG
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