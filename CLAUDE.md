# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**Read [PROGRESS.md](PROGRESS.md) first.** It is the living status document maintained by both developers. It records which phases are complete, what is stubbed, what is in-progress, and what is next. Always check it before implementing anything so you don't duplicate or conflict with the other developer's work.

When asked to implement anything, treat the docs in `/docs` as the source of truth — do not invent architecture, event names, schema fields, or API shapes. If a detail is missing, check the relevant spec doc before guessing.

## Specification Documents (read order matters)

The docs are layered. For most implementation tasks, load context in this order:

1. [docs/project_overview.md](docs/project_overview.md) — what the system is and isn't
2. [docs/architecture.md](docs/architecture.md) — service boundaries, event-driven model
3. [docs/repo_structure.md](docs/repo_structure.md) — canonical folder layout (must follow exactly)
4. [docs/event_flow.md](docs/event_flow.md) — event names, payloads, ownership
5. [docs/database_schema.md](docs/database_schema.md) — MongoDB collections + per-service ownership
6. [docs/api_contracts.md](docs/api_contracts.md) — REST endpoints, response envelope
7. [docs/workflows.md](docs/workflows.md) — end-to-end orchestration steps
8. [docs/agents.md](docs/agents.md) — LangGraph agent contracts (input/output/confidence)
9. [docs/engineering_guidelines.md](docs/engineering_guidelines.md) — naming, logging, conventions
10. [docs/implementation_plan.md](docs/implementation_plan.md) — phased delivery + ownership split
11. [docs/prompts.md](docs/prompts.md) — AI collaboration patterns

## High-Level Architecture

DependencyMedic is an **event-driven autonomous remediation orchestrator** built around five backend services that communicate exclusively through Redis Streams:

```
vuln_intelligence  →  reachability_analysis  →  remediation_engine  →  gitlab_integration
                                                                              ↓
                                          api_gateway  ←  (all services)  →  MongoDB
                                              ↓
                                          frontend (React)
```

### Critical invariants enforced by the specs

- **No direct cross-service DB access.** Each MongoDB collection has exactly one owning service ([docs/database_schema.md](docs/database_schema.md) ownership table). Other services interact via events or APIs.
- **Events follow `domain.action` naming** (`vuln.discovered`, `patch.generated`, `ci.failed`, `mr.created`). Only the domain owner emits its events ([docs/event_flow.md](docs/event_flow.md) ownership table).
- **Every event carries a `correlation_id`** that propagates through the entire CVE → MR workflow for tracing/replay.
- **Deterministic tooling runs before LLMs.** SBOM generation, dependency resolution, log parsing, and version matching are deterministic. LLMs are only used for contextual reasoning, summarization, and CI failure root-cause inference.
- **Max 2 retry attempts** for any agent or CI recovery loop. After that, escalate to human review.
- **Every agent emits a `confidence_score` (0.0–1.0)** and structured JSON output following the shared shape in [docs/agents.md](docs/agents.md).
- **Human approval is mandatory before merge.** Agents may open MRs but never merge.
- **Shared schemas live in `backend/services/shared/`** — never duplicate DTOs/event payloads across services.

### The end-to-end demo flow

`vuln.discovered → vuln.matched → vuln.assessed → vuln.scored → patch.generated → ci.started → (ci.failed → patch.retry_requested →) patch.validated → mr.created`

This sequence is the spine of the hackathon demo. Phase 5 (CI failure recovery via the CI Failure Analysis agent) is explicitly called out as the most important demonstration of autonomy.

## Conventions That Are Easy to Get Wrong

- **API response envelope** is always `{ success, data, error }` — never return raw payloads ([docs/api_contracts.md](docs/api_contracts.md)).
- **All MongoDB documents** must include `created_at`, `updated_at`, `created_by`, `version` ([docs/engineering_guidelines.md](docs/engineering_guidelines.md)).
- **File naming:** Python files `snake_case`; React components `PascalCase.tsx`; tests `test_<feature>.py`.
- **All IO is async.** No blocking calls inside FastAPI routes. External calls require timeouts + exponential backoff.
- **Logging is structured only** — `logger.info("...", extra={...})`, never `print`.
- **API base path is `/api/v1`** with FastAPI Swagger at `/docs`.

## MVP Scope Boundaries (do not cross without asking)

Forbidden in MVP per [docs/engineering_guidelines.md](docs/engineering_guidelines.md) and [docs/implementation_plan.md](docs/implementation_plan.md):
Kubernetes, Kafka, GraphQL, gRPC, service mesh, event-sourcing frameworks, complex ORM layers, multi-tenancy, RBAC systems, production deployment automation, runtime exploit detection, autonomous merging.

The system targets local Docker Compose for development and Google Cloud Run for the demo deployment — nothing more.

## Build / Run / Test Commands

No code or `Makefile` exists yet. Per [docs/repo_structure.md](docs/repo_structure.md), the planned commands are:

```bash
make up          # docker-compose up the full stack
make test        # run backend tests
make lint        # lint backend + frontend
make seed-demo   # seed demo vulnerabilities and repos
```

When implementing Phase 1, create the `Makefile`, `docker-compose.yml`, and `.env.example` (with `MONGO_URI`, `REDIS_URL`, `GITLAB_TOKEN`, `GEMINI_API_KEY`) before any service code.

## Tech Stack (fixed — do not substitute)

Backend: FastAPI, Python 3.11+, MongoDB, Redis Streams, LangGraph, Gemini.
Frontend: React, TypeScript, TailwindCSS, Vite.
Infra: Docker Compose (local), Google Cloud Run (deploy).

## Ownership Model

Two-developer feature-vertical split ([docs/implementation_plan.md](docs/implementation_plan.md)):
- **Developer A** — Threat Intelligence: `vuln_intelligence`, `reachability_analysis`, `vuln.*` events.
- **Developer B** — Remediation: `remediation_engine`, `gitlab_integration`, `patch.*` / `ci.*` / `mr.*` events.
- **Shared** — `backend/services/shared/`, event contracts, Docker Compose, demo scenarios.
