# DependencyMedic — Engineering Guidelines

This document defines the engineering conventions, architectural constraints, naming standards, and implementation rules for the DependencyMedic codebase.

The goal is:

* consistency,
* maintainability,
* predictable AI-assisted development,
* low integration friction,
* and prevention of architectural drift during rapid hackathon iteration.

All contributors and AI coding agents must follow these conventions.

---

# Core Engineering Principles

1. Keep implementations simple and modular.
2. Prefer readability over clever abstractions.
3. Prefer deterministic logic over LLM reasoning whenever possible.
4. Services communicate through APIs or events only.
5. No direct cross-service database access.
6. Shared contracts must live inside `/shared`.
7. Every autonomous action must be explainable.
8. Avoid premature optimization.
9. Keep workflows observable and debuggable.
10. The entire system must remain locally runnable using Docker Compose.

---

# MVP Constraints

The hackathon MVP intentionally avoids unnecessary complexity.

## Allowed

* FastAPI
* MongoDB
* Redis Streams
* LangGraph
* React
* TailwindCSS
* Docker Compose

## Forbidden (MVP)

* Kubernetes
* Kafka
* GraphQL
* gRPC
* Microservice mesh
* Event sourcing frameworks
* Complex ORM abstractions
* Premature distributed scaling

---

# Repository Structure

```text id="b9r0c7"
dependency-medic/
│
├── backend/
│   ├── services/
│   │   ├── vuln_intelligence/
│   │   ├── remediation_engine/
│   │   ├── shared/
│   │   └── api_gateway/
│   │
│   ├── tests/
│   └── scripts/
│
├── frontend/
├── infra/
├── docs/
└── demo/
```

---

# Python Conventions

## File Naming

Use `snake_case`.

Correct:

```python id="o7pvzt"
vulnerability_service.py
patch_generator.py
gitlab_client.py
```

Incorrect:

```python id="d53psk"
PatchGenerator.py
gitLabClient.py
```

---

## Class Naming

Use `PascalCase`.

```python id="5f3y3v"
class VulnerabilityService:
class PatchGenerationAgent:
class GitLabPipelineClient:
```

---

## Function Naming

Use `snake_case`.

Function names must start with action verbs.

Correct:

```python id="ewib9n"
generate_patch()
create_merge_request()
analyze_pipeline_failure()
publish_event()
```

Avoid vague names:

```python id="m3ytnq"
handle()
run()
process()
execute()
```

---

## Variable Naming

Use descriptive names.

Correct:

```python id="9qq85r"
vulnerability_id
pipeline_status
patch_confidence_score
```

Avoid:

```python id="fov8cf"
data
obj
temp
val
```

---

# API Conventions

## REST Naming

Use plural resource names.

```text id="17qfx0"
GET /vulnerabilities
GET /repositories
POST /merge-requests
```

---

## Response Format

All API responses must follow:

```json id="nwv0bl"
{
  "success": true,
  "data": {},
  "error": null
}
```

---

## Error Format

```json id="6c70vi"
{
  "success": false,
  "data": null,
  "error": {
    "code": "PIPELINE_FAILED",
    "message": "Pipeline validation failed"
  }
}
```

---

# Event Conventions

## Event Naming Format

```text id="9j8zy2"
domain.action
```

Examples:

```text id="m3k77o"
vuln.discovered
vuln.assessed
patch.generated
ci.failed
mr.created
```

---

## Event Structure

All events must contain:

```json id="4wr2zq"
{
  "event_id": "uuid",
  "event_type": "vuln.discovered",
  "timestamp": "ISO8601",
  "source_service": "vuln_intelligence",
  "payload": {}
}
```

---

# Agent Design Rules

Each agent must:

* have a single responsibility,
* expose deterministic inputs and outputs,
* emit structured outputs,
* produce confidence scores,
* log reasoning traces,
* avoid hidden side effects.

---

# Database Conventions

## Collection Naming

Use plural `snake_case`.

Examples:

```text id="x9h2gn"
vulnerabilities
repositories
patch_attempts
pipeline_runs
events
```

---

## Required Metadata Fields

Every document must contain:

```json id="w3ll9z"
{
  "created_at": "",
  "updated_at": "",
  "created_by": "",
  "version": 1
}
```

---

# Logging Standards

Use structured logs only.

Correct:

```python id="gg2fht"
logger.info(
    "Patch generated",
    extra={
        "repo_id": repo_id,
        "vulnerability_id": vulnerability_id,
        "confidence": confidence
    }
)
```

Avoid:

```python id="v6y4z0"
print("Patch generated")
```

---

# Async Conventions

* All IO-heavy operations must be async.
* Avoid blocking calls inside FastAPI routes.
* External API calls must use timeouts.
* Retry logic must use exponential backoff.

---

# Shared Types

All shared schemas and DTOs must live inside:

```text id="t6c7xu"
backend/services/shared/
```

Examples:

* Vulnerability
* EventPayload
* PatchResult
* PipelineStatus

No duplicate schema definitions across services.

---

# Environment Variables

All environment variables:

* must be uppercase,
* must be documented,
* and must exist inside `.env.example`.

Example:

```env id="d48e7u"
MONGO_URI=
REDIS_URL=
GITLAB_TOKEN=
GEMINI_API_KEY=
```

---

# Testing Rules

Every feature must include:

* unit tests,
* integration tests,
* and deterministic demo scenarios.

Critical workflows must support:

* local execution,
* reproducible testing,
* and integration validation.

---

# Frontend Conventions

## Component Naming

Use `PascalCase`.

```text id="x0hqqr"
VulnerabilityCard.tsx
PipelineStatusPanel.tsx
```

---

## Hooks

Use:

```text id="2dzb57"
useVulnerabilities()
usePipelineStatus()
```

---

# Git Workflow

## Branch Naming

```text id="jlwmv4"
feature/<feature-name>
fix/<bug-name>
refactor/<area>
```

Examples:

```text id="v3y22r"
feature/gitlab-integration
feature/vulnerability-ingestion
fix/pipeline-retry-logic
```

---

# Definition of Done

A feature is considered complete only if:

* functionality works locally,
* tests pass,
* events are emitted correctly,
* API contracts are respected,
* logs are structured,
* and integration flow works end-to-end.

---

# AI-Assisted Development Rules

When generating code using AI:

* preserve existing architecture,
* reuse shared types,
* avoid introducing new frameworks,
* avoid unnecessary abstractions,
* prefer modifying existing modules over creating duplicates.

All generated code must remain:

* readable,
* modular,
* debuggable,
* and consistent with this document.
