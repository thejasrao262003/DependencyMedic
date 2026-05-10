# Session: Phase 1 — Foundation Setup

**Date:** 2026-05-10  
**Developer:** Varun (Dev A — Threat Intelligence)  
**Phase:** 1 — Foundation Setup  
**Status:** Complete

---

## What was done this session

### Infrastructure
- [x] `docker-compose.yml` — MongoDB 7.0, Redis 7.2, all 5 backend services, frontend
- [x] `Makefile` — `make up`, `make down`, `make test`, `make lint`, `make seed-demo`
- [x] `.env.example` — `MONGO_URI`, `REDIS_URL`, `GITLAB_TOKEN`, `GEMINI_API_KEY`, `GITLAB_URL`
- [x] `backend/Dockerfile` — Python 3.11 image, installs from `requirements/base.txt`
- [x] `frontend/Dockerfile` — Node 20 image, Vite dev server

### `backend/shared/` — frozen contract layer
- [x] `events/base.py` — `BaseEvent(event_id, event_type, timestamp, source_service, correlation_id, payload)`
- [x] `events/vuln_events.py` — `VulnDiscoveredPayload`, `VulnMatchedPayload`, `VulnAssessedPayload`, `VulnScoredPayload`
- [x] `events/patch_events.py` — `PatchGeneratedPayload`, `PatchRetryRequestedPayload`, `PatchValidatedPayload`
- [x] `events/ci_events.py` — `CiStartedPayload`, `CiFailedPayload`
- [x] `events/mr_events.py` — `MrCreatedPayload`
- [x] `schemas/response.py` — `APIResponse[T]` with `.ok()` / `.fail()`
- [x] `schemas/vulnerability.py` — `VulnerabilitySchema`, `AffectedPackage`
- [x] `schemas/repository.py` — `RepositorySchema`
- [x] `schemas/patch.py` — `PatchAttemptSchema`
- [x] `models/base.py` — `BaseDocument(created_at, updated_at, created_by, version)` with `to_mongo()` / `from_mongo()`
- [x] `enums/severity.py` — `Severity` (critical, high, medium, low, informational)
- [x] `enums/status.py` — `VulnStatus`, `RepoStatus`, `PatchStatus`, `PipelineStatus`, `MRStatus`, `AgentRunStatus`
- [x] `constants/__init__.py` — all Redis stream names, MongoDB collection names, `MAX_RETRY_ATTEMPTS = 2`
- [x] `utils/mongo.py` — `init_db()`, `close_db()`, `get_database()`
- [x] `utils/redis_streams.py` — `RedisStreamPublisher`, `RedisStreamConsumer` (consumer groups)
- [x] `logging/logger.py` — `get_logger(service_name)` — structured JSON output

### Backend service skeletons (health endpoints + lifespan only)
- [x] `vuln_intelligence` — port 8001, `/api/v1/health`, connects to MongoDB + Redis on startup
- [x] `reachability_analysis` — port 8002, `/api/v1/health`
- [x] `remediation_engine` — port 8003, `/api/v1/health`
- [x] `gitlab_integration` — port 8004, `/api/v1/health`
- [x] `api_gateway` — port 8000, all 13 REST routes wired to MongoDB:
  - `GET /api/v1/vulnerabilities` — paginated, severity+status filter
  - `GET /api/v1/vulnerabilities/{id}`
  - `GET /api/v1/repositories` + `/{id}`
  - `GET /api/v1/remediations` + `/{id}`
  - `POST /api/v1/remediations/generate` — **stub** (returns 202 placeholder)
  - `GET /api/v1/pipelines` + `/{id}`
  - `GET /api/v1/merge-requests` + `/{id}`
  - `GET /api/v1/events`
  - `GET /api/v1/health` — pings MongoDB + Redis

### Frontend
- [x] Vite + React 18 + TypeScript + TailwindCSS (dark theme)
- [x] `App.tsx` — sidebar nav + routing (React Router)
- [x] `DashboardPage.tsx` — stat cards (vulns/repos/patches/MRs) + service health dots
- [x] `VulnerabilitiesPage.tsx` — stub
- [x] `RemediationsPage.tsx` — stub
- [x] `PipelinesPage.tsx` — stub
- [x] `services/api.ts` — axios client pointed at `VITE_API_BASE_URL`
- [x] `types/index.ts` — shared TypeScript interfaces

### Demo & tests
- [x] `backend/scripts/seed_demo.py` — seeds Log4Shell (CVE-2021-44228, CVE-2021-45046) + 3 demo repos
- [x] `demo/seed_data/critical_cve.json` — raw CVE fixture
- [x] `backend/tests/unit/test_shared_events.py` — event schema unit tests
- [x] `backend/tests/conftest.py` — pytest fixtures skeleton

### Infrastructure verified
- [x] `make up` runs successfully — all containers start
- [x] MongoDB healthcheck passes (logs confirmed normal — healthcheck pings via mongosh)
- [x] Redis healthcheck passes

---

## What is NOT done (stubs / empty dirs)

All service business logic directories are empty `__init__.py` stubs:
- `vuln_intelligence/services/`, `vuln_intelligence/agents/`, `vuln_intelligence/consumers/`, `vuln_intelligence/producers/`
- `reachability_analysis/analyzers/`, `reachability_analysis/scanners/`, `reachability_analysis/agents/`
- `remediation_engine/patchers/`, `remediation_engine/ci_analysis/`, `remediation_engine/retry_engine/`, `remediation_engine/agents/`
- `gitlab_integration/clients/`, `gitlab_integration/merge_requests/`, `gitlab_integration/pipelines/`, `gitlab_integration/webhooks/`

Frontend pages beyond Dashboard are empty stubs.

`POST /remediations/generate` always returns a placeholder — not wired to any service.

---

## Next session (Phase 2 — Vulnerability Intelligence)

Planned work for Dev A:
- NVD API ingestion (`vuln_intelligence/services/nvd_ingestion.py`)
- OSV API ingestion (`vuln_intelligence/services/osv_ingestion.py`)
- CVE normalisation + deduplication into `vulnerabilities` collection
- Repository registration (GitLab repo sync or manual registration)
- SBOM / dependency file parsing (`requirements.txt`, `pom.xml`, `package.json`)
- Repository matching against affected packages
- Publish `vuln.discovered` → Redis Stream
- Publish `vuln.matched` → Redis Stream
- Populate Vulnerabilities page in frontend

---

## Key decisions made

- `backend/shared/` event schemas are frozen — coordinate with Dev B before changing
- MongoDB auth is off in dev (no credentials) — expected and intentional
- `correlation_id` flows through every event from `vuln.discovered` to `mr.created`
- Max 2 retries enforced via `MAX_RETRY_ATTEMPTS = 2` in `shared/constants`
