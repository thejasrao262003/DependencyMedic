# DependencyMedic — Shared Progress Log

> **How to use this file:** Update this doc on every meaningful commit or when a phase completes.
> Both developers' Claude instances read this to get current context without re-reading the full codebase.
> Keep entries concrete — what works, what is stubbed, what is next.

---

## Team

| Role | Domain | Services |
|------|--------|----------|
| **Dev A** (Varun) | Threat Intelligence | `vuln_intelligence`, `reachability_analysis` |
| **Dev B** | Remediation | `remediation_engine`, `gitlab_integration` |
| **Shared** | Infrastructure, contracts, demo | `api_gateway`, `backend/shared/`, Docker, frontend |

---

## Phase Status

| Phase | Name | Status | Owner |
|-------|------|--------|-------|
| 1 | Foundation Setup | ✅ Complete | Shared |
| 2 | Vulnerability Intelligence | 🔲 Not started | Dev A |
| 3 | Reachability & Risk Analysis | 🔲 Not started | Dev A |
| 4 | Patch Generation & GitLab Integration | 🔲 Not started | Dev B |
| 5 | CI Failure Recovery | 🔲 Not started | Dev B |
| 6 | Demo Readiness & Polish | 🔲 Not started | Shared |

---

## Phase 1 — Foundation Setup ✅

**Completed by:** Shared  
**Date:** 2026-05-10

### What was built

#### Infrastructure
- `docker-compose.yml` — MongoDB 7.0, Redis 7.2, all 5 backend services, frontend
- `Makefile` — `make up`, `make test`, `make lint`, `make seed-demo`
- `.env.example` — `MONGO_URI`, `REDIS_URL`, `GITLAB_TOKEN`, `GEMINI_API_KEY`, `GITLAB_URL`
- `backend/Dockerfile`, `frontend/Dockerfile`

#### `backend/shared/` — Frozen contract layer (do not modify without coordinating both devs)
- `events/base.py` — `BaseEvent` with `event_id`, `event_type`, `timestamp`, `source_service`, `correlation_id`, `payload`
- `events/vuln_events.py` — `VulnDiscoveredPayload`, `VulnMatchedPayload`, `VulnAssessedPayload`, `VulnScoredPayload`
- `events/patch_events.py` — `PatchGeneratedPayload`, `PatchRetryRequestedPayload`, `PatchValidatedPayload`
- `events/ci_events.py` — `CiStartedPayload`, `CiFailedPayload`
- `events/mr_events.py` — `MrCreatedPayload`
- `schemas/response.py` — `APIResponse[T]` with `.ok()` / `.fail()` — **used by every route**
- `schemas/vulnerability.py` — `VulnerabilitySchema`, `AffectedPackage`
- `schemas/repository.py` — `RepositorySchema`
- `schemas/patch.py` — `PatchAttemptSchema`
- `models/base.py` — `BaseDocument` with `created_at`, `updated_at`, `created_by`, `version`, `to_mongo()`, `from_mongo()`
- `enums/severity.py` — `Severity` (critical, high, medium, low)
- `enums/status.py` — `VulnStatus`, `RepoStatus`, `PatchStatus`, `PipelineStatus`, `MRStatus`, `AgentRunStatus`
- `constants/__init__.py` — all stream names (`STREAM_VULN_DISCOVERED`, etc.), collection names, `MAX_RETRY_ATTEMPTS = 2`
- `utils/mongo.py` — `init_db()`, `close_db()`, `get_database()`
- `utils/redis_streams.py` — `RedisStreamPublisher`, `RedisStreamConsumer` (consumer groups), `get_redis()`, `close_redis()`
- `logging/logger.py` — `get_logger(service_name)` — structured JSON logger

#### Backend services (skeletons only — health endpoint + lifespan wiring)
| Service | Port | What works | What's stubbed |
|---------|------|-----------|----------------|
| `api_gateway` | 8000 | All 13 REST routes reading from MongoDB, `/health` checks Mongo+Redis | `POST /remediations/generate` returns placeholder |
| `vuln_intelligence` | 8001 | `/health`, MongoDB + Redis connect | Everything else |
| `reachability_analysis` | 8002 | `/health`, MongoDB + Redis connect | Everything else |
| `remediation_engine` | 8003 | `/health`, MongoDB + Redis connect | Everything else |
| `gitlab_integration` | 8004 | `/health`, MongoDB + Redis connect | Everything else |

#### `api_gateway` routes (all wired to MongoDB, functional for CRUD):
- `GET/GET /{id} /vulnerabilities` — reads `vulnerabilities` collection, supports severity/status filter + pagination
- `GET/GET /{id} /repositories` — reads `repositories` collection
- `GET/GET /{id} /remediations` — reads `patch_attempts` collection
- `POST /remediations/generate` — placeholder (returns 202 with not-implemented message)
- `GET/GET /{id} /pipelines` — reads `pipeline_runs` collection
- `GET/GET /{id} /merge-requests` — reads `merge_requests` collection
- `GET /events` — reads `events` collection
- `GET /health` — pings MongoDB + Redis, returns `{ status, services }`

#### Frontend (`frontend/src/`)
- Vite + React 18 + TypeScript + TailwindCSS (dark theme, gray-900 base)
- `App.tsx` — routing with sidebar nav
- `pages/DashboardPage.tsx` — stat cards (vulns, repos, patches, MRs) + service health indicators
- `pages/VulnerabilitiesPage.tsx` — stub
- `pages/RemediationsPage.tsx` — stub
- `pages/PipelinesPage.tsx` — stub
- `services/api.ts` — axios client pointed at `VITE_API_BASE_URL`
- `types/index.ts` — shared TypeScript types

#### Demo / Tests
- `backend/scripts/seed_demo.py` — seeds Log4Shell (CVE-2021-44228, CVE-2021-45046) + 3 demo repos (payment-service, auth-service, inventory-service)
- `demo/seed_data/critical_cve.json` — raw CVE fixture
- `backend/tests/unit/test_shared_events.py` — event schema unit tests
- `backend/tests/conftest.py` — pytest fixtures

### How to run
```bash
cp .env.example .env          # fill GITLAB_TOKEN, GEMINI_API_KEY
make up                        # docker-compose up --build -d
make seed-demo                 # load Log4Shell + 3 demo repos
```
- Dashboard: http://localhost:3000
- API + Swagger: http://localhost:8000/docs

---

## Phase 2 — Vulnerability Intelligence 🔲

**Owner:** Dev A  
**Status:** Not started  
**Target events:** `vuln.discovered`, `vuln.matched`

### Planned deliverables
- [ ] NVD API ingestion (`vuln_intelligence/services/nvd_ingestion.py`)
- [ ] OSV API ingestion (`vuln_intelligence/services/osv_ingestion.py`)
- [ ] CVE normalisation + deduplication
- [ ] Repository registration API / GitLab repo sync
- [ ] SBOM generation (dependency file parsing — `requirements.txt`, `pom.xml`, `package.json`)
- [ ] Repository matching (which repos use affected packages)
- [ ] Publish `vuln.discovered` → Redis Stream
- [ ] Publish `vuln.matched` → Redis Stream
- [ ] Frontend: populated Vulnerabilities page (table, severity filter)

---

## Phase 3 — Reachability & Risk Analysis 🔲

**Owner:** Dev A  
**Status:** Not started  
**Target events:** `vuln.assessed`, `vuln.scored`

### Planned deliverables
- [ ] Consumes `vuln.matched` from Redis Stream
- [ ] Dependency graph traversal (reachability check)
- [ ] Reachability agent (LangGraph + Gemini) — emits `confidence_score`
- [ ] CVSS + EPSS integration for risk scoring
- [ ] Publish `vuln.assessed`, `vuln.scored` → Redis Stream
- [ ] Frontend: risk scores on vulnerability detail view

---

## Phase 4 — Patch Generation & GitLab Integration 🔲

**Owner:** Dev B  
**Status:** Not started  
**Target events:** `patch.generated`, `ci.started`

### Planned deliverables
- [ ] Consumes `vuln.scored` from Redis Stream
- [ ] GitLab API client (`gitlab_integration/clients/gitlab_client.py`)
- [ ] Patch generation (dependency upgrade manifests — `remediation_engine/patchers/`)
- [ ] Branch creation + commit push via GitLab API
- [ ] CI pipeline trigger
- [ ] MR creation (draft, not merged)
- [ ] Publish `patch.generated`, `ci.started` → Redis Stream
- [ ] Frontend: Remediations page with branch + pipeline status

---

## Phase 5 — CI Failure Recovery 🔲

**Owner:** Dev B  
**Status:** Not started  
**Target events:** `ci.failed`, `patch.retry_requested`, `patch.validated`, `mr.created`

### Planned deliverables
- [ ] GitLab CI webhook handler (receives pipeline status)
- [ ] CI log collection from GitLab API
- [ ] CI Failure Analysis agent (LangGraph + Gemini) — classifies failure, emits root cause + `confidence_score`
- [ ] Retry engine (max 2 attempts per `MAX_RETRY_ATTEMPTS`)
- [ ] Adjusted patch generation on retry
- [ ] Publish `ci.failed`, `patch.retry_requested`, `patch.validated`, `mr.created`
- [ ] Frontend: Pipelines page with timeline, retry visualisation

---

## Phase 6 — Demo Readiness 🔲

**Owner:** Shared  
**Status:** Not started

### Planned deliverables
- [ ] Deterministic demo scenario scripts
- [ ] Frontend polish — workflow timeline, event feed, correlation ID tracing
- [ ] Structured log + event inspection UI
- [ ] Cloud Run deployment (optional)
- [ ] Demo walkthrough script + narration points

---

## Key Decisions & Constraints

| Decision | Detail |
|----------|--------|
| Max retry attempts | 2 (enforced by `MAX_RETRY_ATTEMPTS` constant) |
| Human approval | Mandatory before any MR merge — agents open MRs, never merge |
| LLM usage | Only for reachability reasoning, CI failure root cause, and summarisation — never for deterministic steps |
| Event naming | `domain.action` — only the domain owner emits its events |
| `correlation_id` | Every event carries one; propagates through the full CVE → MR flow |
| Shared schemas | Live exclusively in `backend/shared/` — never duplicate across services |
| API envelope | Always `{ success, data, error }` — never raw payloads |
| MongoDB fields | Every document: `created_at`, `updated_at`, `created_by`, `version` |
| Out of scope | Kubernetes, Kafka, GraphQL, gRPC, autonomous merging, multi-tenancy |

---

## Stream Names (quick reference)

```
vuln.discovered        → published by: vuln_intelligence      → consumed by: reachability_analysis
vuln.matched           → published by: vuln_intelligence      → consumed by: reachability_analysis
vuln.assessed          → published by: reachability_analysis  → consumed by: remediation_engine
vuln.scored            → published by: reachability_analysis  → consumed by: remediation_engine
patch.generated        → published by: remediation_engine     → consumed by: gitlab_integration
ci.started             → published by: gitlab_integration      → consumed by: remediation_engine
ci.failed              → published by: gitlab_integration      → consumed by: remediation_engine
patch.retry_requested  → published by: remediation_engine     → consumed by: gitlab_integration
patch.validated        → published by: remediation_engine     → consumed by: gitlab_integration
mr.created             → published by: gitlab_integration      → consumed by: api_gateway
```

---

## MongoDB Collections (quick reference)

| Collection | Owner service | Purpose |
|------------|---------------|---------|
| `vulnerabilities` | vuln_intelligence | CVE records |
| `repositories` | vuln_intelligence | Registered repos |
| `dependency_snapshots` | reachability_analysis | SBOM snapshots |
| `risk_assessments` | reachability_analysis | Reachability + CVSS/EPSS scores |
| `patch_attempts` | remediation_engine | Patch generation attempts |
| `pipeline_runs` | gitlab_integration | CI pipeline runs |
| `merge_requests` | gitlab_integration | MR records |
| `events` | api_gateway | Event log (read-only replay) |
| `agent_runs` | (owning service) | Agent execution records |
