# DependencyMedic — Consolidated Specification

> Single-document specification distilled from the eleven design docs in [docs/](docs/). Use this as a quick reference; the per-topic docs remain authoritative for details.

---

## 1. Product Definition

**DependencyMedic** is an autonomous AI-powered software supply chain defense system built for the Google Cloud Rapid Agent Hackathon. It behaves like an AI Security Engineer: continuously monitoring vulnerability feeds, identifying impacted GitLab repositories, reasoning about exploitability, generating dependency remediation patches, validating them through GitLab CI/CD, and orchestrating merge requests with human approval gates.

It is **not** a chatbot, a vulnerability dashboard, or a simple dependency updater. The differentiator is **autonomous orchestration of remediation workflows end-to-end**, including CI self-healing.

### Core capabilities

| Capability                       | Behavior                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------ |
| Vulnerability Intelligence       | Ingest NVD / OSV.dev / GHSA, normalize, deduplicate, track exploitability     |
| Repository & Dependency Analysis | Scan GitLab repos, generate SBOMs, build dependency graphs                    |
| Exploitability Reasoning         | Determine if vulnerable code is reachable; combine deterministic + LLM        |
| Autonomous Patch Generation      | Upgrade dependencies, update manifests, regenerate lockfiles                  |
| GitLab CI/CD Orchestration       | Trigger pipelines, analyze failures, retry with adjusted patches              |
| Merge Request Automation         | Open MRs with reasoning traces and rollback guidance, assign reviewers        |
| Human-Supervised Safety          | Confidence scoring, mandatory human approval before merge, full audit trail   |

---

## 2. Architectural Principles

1. Event-driven workflows over tight coupling.
2. Specialized agents over a monolithic orchestrator.
3. Deterministic tooling before LLM reasoning.
4. Human-supervised autonomy over unrestricted automation.
5. Shared contracts over implicit integrations.
6. Local-first development (Docker Compose).
7. Demo realism over production-scale complexity.

---

## 3. System Architecture

```
            Vulnerability Feeds (NVD / OSV / GHSA)
                          │
                          ▼
              ┌───────────────────────┐
              │  vuln_intelligence    │
              └──────────┬────────────┘
                         ▼
                ┌─────────────────┐
                │ Redis Streams   │
                └────────┬────────┘
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌─────────────────────┐         ┌────────────────────┐
│ reachability_       │         │ remediation_engine │
│ analysis            │         │ + ci_failure_      │
│ (SBOM, risk score)  │         │   analysis         │
└─────────┬───────────┘         └─────────┬──────────┘
          │                                │
          ▼                                ▼
   ┌────────────┐               ┌───────────────────┐
   │  MongoDB   │               │ gitlab_integration│
   └────────────┘               │ (pipelines, MRs)  │
                                └─────────┬─────────┘
                                          ▼
                                ┌───────────────────┐
                                │ api_gateway       │
                                └─────────┬─────────┘
                                          ▼
                                ┌───────────────────┐
                                │ React Dashboard   │
                                └───────────────────┘
```

### 3.1 Backend services

| Service                 | Responsibilities                                                          | Owns Collections                          | Emits Events                                |
| ----------------------- | ------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------- |
| `vuln_intelligence`     | CVE ingestion, normalization, dedup, repo matching                        | `vulnerabilities`                         | `vuln.discovered`, `vuln.matched`           |
| `reachability_analysis` | SBOM generation, dependency graphing, exploitability, risk scoring        | `dependency_snapshots`, `risk_assessments`| `vuln.assessed`, `vuln.scored`              |
| `remediation_engine`    | Patch generation, manifest/lockfile updates, retry orchestration          | `patch_attempts`                          | `patch.generated`, `patch.validated`, `patch.retry_requested` |
| `gitlab_integration`    | Repo sync, branch/commit, MR creation, CI triggering, webhook handling    | `repositories`, `merge_requests`          | `ci.started`, `pipeline.completed`, `ci.failed`, `mr.created` |
| `api_gateway`           | Frontend-facing REST aggregation, auth middleware                         | —                                         | —                                           |

`event_system` owns the `events` collection; `langgraph_runtime` owns `agent_runs`.

### 3.2 Frontend

React + TypeScript + TailwindCSS + Vite. Pages: dashboard, vulnerability details, repository view, pipeline timeline, MR approval. Consumes only `/api/v1` endpoints; no direct service calls.

---

## 4. Technology Stack

| Layer            | Choice                                |
| ---------------- | ------------------------------------- |
| Backend          | FastAPI, Python 3.11+, async I/O      |
| Database         | MongoDB                               |
| Event bus        | Redis Streams                         |
| Agent framework  | LangGraph                             |
| LLM              | Gemini                                |
| Frontend         | React, TypeScript, TailwindCSS, Vite  |
| Local infra      | Docker Compose                        |
| Deploy target    | Google Cloud Run                      |

**Forbidden in MVP:** Kubernetes, Kafka, GraphQL, gRPC, service mesh, event-sourcing frameworks, complex ORM layers, multi-tenancy, advanced RBAC, production deployment automation.

---

## 5. Repository Layout

```
dependency-medic/
├── backend/
│   ├── services/
│   │   ├── vuln_intelligence/
│   │   ├── reachability_analysis/
│   │   ├── remediation_engine/
│   │   ├── gitlab_integration/
│   │   └── api_gateway/
│   ├── shared/        # events/, schemas/, models/, enums/, utils/, logging/
│   ├── tests/         # unit/, integration/, e2e/, fixtures/, mocks/
│   ├── scripts/
│   └── pyproject.toml
├── frontend/
│   └── src/           # components/, pages/, hooks/, services/, stores/, types/
├── infra/             # docker/, cloud_run/, monitoring/, nginx/
├── demo/              # vulnerable_services/, demo_scenarios/, seed_data/
├── docs/
├── scripts/
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

Per-service inner layout (typical): `api/ services/ consumers/ producers/ models/ schemas/ agents/ utils/ config/ main.py`. Full breakdown in [docs/repo_structure.md](docs/repo_structure.md).

**Forbidden patterns:** deeply nested utility folders, duplicate schemas across services, service-to-service DB access, circular imports, scripts outside `/scripts`, unstructured event payloads.

---

## 6. Event Contract

### Naming
`domain.action` — e.g. `vuln.discovered`, `patch.generated`, `ci.failed`.

### Standard envelope
```json
{
  "event_id": "uuid",
  "event_type": "vuln.discovered",
  "timestamp": "ISO8601",
  "source_service": "vuln_intelligence",
  "correlation_id": "workflow_uuid",
  "payload": {}
}
```

### Lifecycle (happy path)
```
vuln.discovered → vuln.matched → vuln.assessed → vuln.scored
   → patch.generated → ci.started → pipeline.completed
   → patch.validated → mr.created
```

### Domain ownership
Only the owning service may emit events in its domain.

| Domain    | Owner                |
| --------- | -------------------- |
| `vuln.*`  | `vuln_intelligence`  |
| `patch.*` | `remediation_engine` |
| `ci.*`    | `gitlab_integration` |
| `mr.*`    | `gitlab_integration` |

### Rules
- All events persisted to MongoDB `events` collection.
- Consumers must be **idempotent** (verify processing state, dedupe writes).
- `correlation_id` propagates across the full workflow for tracing/replay.
- Retries use exponential backoff with dead-letter logging.

---

## 7. Database Schema (MongoDB)

Collections: `vulnerabilities`, `repositories`, `dependency_snapshots`, `risk_assessments`, `patch_attempts`, `pipeline_runs`, `merge_requests`, `events`, `agent_runs`.

**Common metadata** required on every document:
```json
{ "created_at": "ISO8601", "updated_at": "ISO8601", "created_by": "service_name", "version": 1 }
```

**Relationship spine:**
```
repositories → dependency_snapshots → risk_assessments → patch_attempts → pipeline_runs → merge_requests
```

Detailed document shapes, indexes, and ownership in [docs/database_schema.md](docs/database_schema.md).

**Schema evolution:** additive changes only during MVP; bump `version` for major structural updates.

---

## 8. API Contract

Base URL: `http://localhost:8000/api/v1`. Swagger at `/docs`.

### Response envelope (all endpoints)
```json
{ "success": true, "data": {}, "error": null }
```

### Error envelope
```json
{ "success": false, "data": null, "error": { "code": "PIPELINE_FAILED", "message": "..." } }
```

### Endpoints (MVP)

| Method | Path                                              | Purpose                              |
| ------ | ------------------------------------------------- | ------------------------------------ |
| GET    | `/vulnerabilities`                                | List CVEs (filter: severity, status) |
| GET    | `/vulnerabilities/{id}`                           | CVE details                          |
| GET    | `/repositories`                                   | List monitored repos                 |
| POST   | `/repositories`                                   | Register a GitLab repo               |
| GET    | `/repositories/{id}/risks`                        | Risk assessments for a repo          |
| POST   | `/remediations/generate`                          | Trigger patch generation             |
| GET    | `/remediations/{patch_attempt_id}`                | Patch attempt status                 |
| GET    | `/pipelines`                                      | List pipeline runs                   |
| GET    | `/pipelines/{id}`                                 | Pipeline details                     |
| GET    | `/merge-requests`                                 | List remediation MRs                 |
| POST   | `/merge-requests/{id}/approve`                    | Approve an MR                        |
| GET    | `/events`                                         | Event audit (filter: type, corr_id)  |
| GET    | `/health`                                         | Liveness + dependency checks         |

### Rules
- Pagination: `page=1, limit=20`, max `limit=100`.
- Auth (MVP): API token from env; GitLab OAuth optional later.
- All requests carry/propagate `correlation_id` for observability.

---

## 9. Workflows

Five orchestrated workflows; each is event-driven, retry-safe, and persists state transitions.

| # | Workflow                  | Trigger              | Key outputs                                         |
| - | ------------------------- | -------------------- | --------------------------------------------------- |
| 1 | Vulnerability Discovery   | Polling (5 min)      | `vuln.discovered`; row in `vulnerabilities`         |
| 2 | Reachability & Risk       | `vuln.discovered`    | `vuln.assessed`, `vuln.scored`; `risk_assessments`  |
| 3 | Patch Generation          | `vuln.scored` (≥med) | `patch.generated`; row in `patch_attempts`          |
| 4 | CI Validation             | `patch.generated`    | `ci.started` → `patch.validated` or `ci.failed`     |
| 5 | CI Failure Recovery       | `ci.failed`          | `patch.retry_requested`, retry pipeline run         |
| 6 | Merge Request Creation    | `patch.validated`    | `mr.created`; row in `merge_requests`              |

Patch generation only runs when `risk_level >= medium`. Retry cap: **2 attempts**, then escalate to human (`requires_human_intervention`).

Every workflow execution shares a `correlation_id` enabling end-to-end tracing and demo replay.

Detailed step-by-step flows in [docs/workflows.md](docs/workflows.md).

---

## 10. Agents

DependencyMedic uses **specialized workflow agents**, not a single monolith. Four MVP agents:

1. **Vulnerability Intelligence Agent** — CVE ingestion, normalization, repo matching.
2. **Reachability Analysis Agent** — SBOM, dependency graph, exploitability, evidence traces.
3. **Patch Generation Agent** — version resolution, branch creation, manifest/lockfile updates.
4. **CI Failure Analysis Agent** — log parsing, root-cause reasoning, retry recommendations.

### Lifecycle (every agent)
```
Input → Validation → Tool Execution → LLM Reasoning → Structured Output
      → Confidence Scoring → Event Emission → Persistence (agent_runs)
```

### Required structured output
```json
{
  "status": "completed",
  "confidence_score": 0.91,
  "summary": "...",
  "actions_taken": [],
  "recommendations": [],
  "requires_human_review": false
}
```

### Determinism boundary
| Allowed for LLM                                     | Forbidden for LLM                              |
| --------------------------------------------------- | ---------------------------------------------- |
| Vulnerability summarization                          | Deterministic dependency matching              |
| Exploitability contextual reasoning                  | Guaranteed exploitability proofs               |
| CI failure root-cause inference                      | Direct production deployment decisions         |
| Migration / compatibility guidance                   | Unrestricted autonomous actions                |

### Universal rules
- Idempotent, retry-safe (max **2** attempts, exponential backoff).
- `confidence_score ∈ [0.0, 1.0]` on every run.
- Persist input/output/duration/tokens/retries to `agent_runs`.
- Agents may open MRs; **agents may never merge**. Human approval is mandatory.

---

## 11. Engineering Conventions

### Python
- Files `snake_case`; classes `PascalCase`; functions `snake_case`, action-verb prefixed (`generate_patch`, not `handle`).
- All IO is async. No blocking calls inside FastAPI routes. External calls require timeouts and exponential-backoff retries.
- Structured logging only: `logger.info("...", extra={...})`. Never `print`.

### Frontend
- Components `PascalCase.tsx` (e.g. `VulnerabilityCard.tsx`).
- Hooks: `useVulnerabilities()`, `usePipelineStatus()`.
- No mock APIs, no hardcoded inline data. Use typed API clients.

### Tests
- `test_<feature>.py` under `backend/tests/{unit,integration,e2e}`.
- E2E target: `CVE → Patch → CI → MR` flow.

### Environment variables
Uppercase, documented, present in `.env.example`:
```
MONGO_URI=
REDIS_URL=
GITLAB_TOKEN=
GEMINI_API_KEY=
```

### Git
- Branches: `feature/<name>`, `fix/<name>`, `refactor/<area>`.
- Commits: `feat(vuln-intelligence): add NVD ingestion workflow`.

### Definition of Done
Functionality runs locally, tests pass, events emit correctly, API contracts respected, logs structured, integration flow works end-to-end.

Full conventions in [docs/engineering_guidelines.md](docs/engineering_guidelines.md).

---

## 12. Implementation Plan

Six phases; each must produce runnable, observable, testable output.

| Phase | Goal                                | Key deliverables                                                              |
| ----- | ----------------------------------- | ----------------------------------------------------------------------------- |
| 1     | Foundation Setup                    | Docker Compose, MongoDB, Redis, FastAPI + React skeletons, shared schemas, Makefile |
| 2     | Vulnerability Intelligence          | NVD/OSV ingestion, repo registration, SBOM, `vuln.discovered`/`vuln.matched`  |
| 3     | Reachability & Risk Analysis        | Graph traversal, CVSS+EPSS scoring, evidence, `vuln.assessed`/`vuln.scored`   |
| 4     | Patch Generation & GitLab Integration | Branch/commit/MR automation, pipeline triggering, `patch.generated`/`ci.started` |
| 5     | CI Failure Recovery                 | Log parsing, retry engine, failure classifier — **demo centerpiece**          |
| 6     | Demo Readiness & Polish             | Seeded vulnerable repos, frontend timeline, demo scripts, replayable flows    |

### Recommended development order
Infrastructure → shared schemas/events → vulnerability ingestion → repo management → SBOM → reachability → risk scoring → patch generation → GitLab integration → CI validation → retry engine → frontend polish → demo prep.

### Ownership split (two developers)

| Developer A — Threat Intelligence            | Developer B — Remediation                       |
| -------------------------------------------- | ----------------------------------------------- |
| `vuln_intelligence`, `reachability_analysis` | `remediation_engine`, `gitlab_integration`      |
| `vuln.*` events                              | `patch.*`, `ci.*`, `mr.*` events                |
| Vulnerability + risk dashboard               | Remediation + MR dashboard                      |

Shared: `backend/services/shared/`, event contracts, Docker Compose, demo scenarios, integration testing.

Full phase exit criteria in [docs/implementation_plan.md](docs/implementation_plan.md).

---

## 13. Demo Vision

The hackathon demo simulates a software organization with multiple intentionally vulnerable microservices, GitLab repos, and CI pipelines. The flow:

```
Critical CVE Published
   ↓
DependencyMedic detects vulnerability
   ↓
Affected repositories identified
   ↓
Exploitability analysis executed
   ↓
Patch generated automatically
   ↓
GitLab CI triggered
   ↓
CI failure diagnosed and retried
   ↓
Merge request opened (with reasoning trace)
   ↓
Human approval workflow
```

Demo emphasis: **visible orchestration, operational intelligence, explainability, autonomous workflow coordination.**

---

## 14. Success Criteria

The MVP is successful if it can, live during the demo:

- ingest real vulnerabilities,
- identify impacted repositories,
- generate working dependency remediation patches,
- trigger GitLab pipelines,
- recover from at least one CI failure autonomously,
- create remediation merge requests, and
- demonstrate the end-to-end orchestration without manual debugging.

---

## 15. Non-Goals

Explicitly excluded from MVP:

- Autonomous production deployment / direct production merges
- Kubernetes orchestration, multi-region scaling, service mesh
- Runtime container security, runtime exploit detection
- First-party (application code) vulnerability remediation
- Multi-tenant SaaS architecture, complex RBAC
- Self-learning autonomous agents, unsupervised production remediation
- Event sourcing frameworks, distributed sagas

---

## 16. Risk Register

| Risk                   | Mitigation                                |
| ---------------------- | ----------------------------------------- |
| GitLab API instability | Local retry logic + mocks                 |
| CI unpredictability    | Controlled, seeded demo repositories      |
| LLM hallucinations     | Deterministic validation gates first      |
| Integration failures   | Event contracts frozen early              |
| Scope explosion        | Strict MVP boundaries (Section 15)        |

---

## 17. Source Documents

| Topic                       | Document                                                  |
| --------------------------- | --------------------------------------------------------- |
| Vision and scope            | [docs/project_overview.md](docs/project_overview.md)      |
| System architecture         | [docs/architecture.md](docs/architecture.md)              |
| Folder layout               | [docs/repo_structure.md](docs/repo_structure.md)          |
| Event bus                   | [docs/event_flow.md](docs/event_flow.md)                  |
| MongoDB schema              | [docs/database_schema.md](docs/database_schema.md)        |
| REST API                    | [docs/api_contracts.md](docs/api_contracts.md)            |
| Workflow orchestration      | [docs/workflows.md](docs/workflows.md)                    |
| Agent contracts             | [docs/agents.md](docs/agents.md)                          |
| Coding conventions          | [docs/engineering_guidelines.md](docs/engineering_guidelines.md) |
| Roadmap and ownership       | [docs/implementation_plan.md](docs/implementation_plan.md)|
| AI prompting patterns       | [docs/prompts.md](docs/prompts.md)                        |
