# Session: Phase 2 — NVD + OSV Ingestion

**Date:** 2026-05-10  
**Developer:** Varun (Dev A — Threat Intelligence)  
**Phase:** 2 — Vulnerability Intelligence (partial)  
**Status:** NVD + OSV ingestion complete, repository matching not yet started

---

## What was done this session

### New files created

| File | Purpose |
|------|---------|
| `vuln_intelligence/services/nvd_ingestion.py` | Fetches CVEs from NVD API v2 by date range + severity. Normalizes to internal schema. |
| `vuln_intelligence/services/osv_ingestion.py` | Queries OSV by CVE ID (enrichment) and by package batch. Extracts affected packages + version ranges. |
| `vuln_intelligence/services/vuln_store.py` | Upserts to `vulnerabilities` collection by `cve_id`. Deduplicates. Writes to `events` collection. |
| `vuln_intelligence/services/ingest_orchestrator.py` | Orchestrates: NVD fetch → OSV enrichment → upsert → publish events. Returns `IngestResult`. |
| `vuln_intelligence/producers/vuln_producer.py` | Publishes `vuln.discovered` and `vuln.matched` to Redis Streams. |
| `vuln_intelligence/api/ingest.py` | `POST /api/v1/ingest` endpoint. Accepts `days_back`, `severities`, `packages`. |

### Files modified

| File | Change |
|------|--------|
| `vuln_intelligence/main.py` | Added `ingest_router` |
| `vuln_intelligence/config.py` | Added `nvd_api_key` setting |
| `api_gateway/config.py` | Added `vuln_intelligence_url`, kept Dev B's `remediation_engine_url` + `gitlab_integration_url` after merge conflict |
| `api_gateway/routes/vulnerabilities.py` | Added `POST /vulnerabilities/ingest` proxy to vuln_intelligence (300s timeout) |
| `.env.example` | Added `NVD_API_KEY=` (empty — real key stays in .env, never committed) |
| `shared/logging/logger.py` | Added `logger.propagate = False` to fix double-log output |
| `scripts/seed_demo.py` | Updated with real GitLab project IDs/URLs for 3 demo repos |
| `frontend/src/App.tsx` | Added RepositoriesPage route + nav link |
| `frontend/src/pages/VulnerabilitiesPage.tsx` | Added ingest button, severity filter tabs, ingest result banner, error display |
| `frontend/src/pages/DashboardPage.tsx` | Fixed repos count bug (was reading vulns response instead of repos response) |

### New frontend files

| File | Purpose |
|------|---------|
| `frontend/src/pages/RepositoriesPage.tsx` | Repo list with language badges, tags, GitLab links, CI status, project ID |

---

## How the ingestion works

```
POST /api/v1/vulnerabilities/ingest (api_gateway:8000)
  → proxies to POST /api/v1/ingest (vuln_intelligence:8001)
    → NVDIngestionService.fetch_recent_cves(days_back, severities)
    → OSVIngestionService.fetch_vulns_for_packages(extra_packages)  [for specific packages only]
    → merge: OSV data enriches NVD records where cve_id matches
    → VulnStore.upsert_vulnerability(vuln_dict) → (vuln_id, is_new)
    → if is_new: VulnProducer.publish_discovered(...)  → Redis stream "vuln.discovered"
    → if is_new: VulnStore.log_event(...)               → MongoDB "events" collection
```

**IMPORTANT**: Per-CVE OSV enrichment was removed. Earlier design called `enrich_with_packages(cve_id)` for every NVD result — this caused 100+ sequential HTTP calls all returning 400 (recent CVEs not indexed by OSV yet), causing the ingest to hang for minutes. OSV is now only queried in batch for the specific packages passed in the request body.

### Example trigger call

```bash
curl -X POST http://localhost:8000/api/v1/vulnerabilities/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 30,
    "severities": ["CRITICAL"],
    "packages": [
      {"name": "log4j-core", "ecosystem": "Maven"},
      {"name": "requests", "ecosystem": "PyPI"}
    ]
  }'
```

### Example response

```json
{
  "success": true,
  "data": {
    "total_fetched": 47,
    "new_stored": 12,
    "updated": 35,
    "events_published": 12,
    "errors": []
  }
}
```

---

## What is NOT done yet (Phase 2 remainder)

- [ ] Repository matching — given `vuln.discovered`, find which repos are affected by scanning their dependency files
- [ ] `vuln.matched` event publishing — happens after repo matching
- [ ] SBOM/dependency file parsing — fetch `requirements.txt`/`pom.xml`/`package.json` from GitLab
- [x] Frontend: populated Vulnerabilities page (ingest button, severity filter, error display)
- [x] GitLab repos seeded with real project IDs/URLs and `seed_manifests` for demo reproducibility

---

## Key decisions made

- **Trigger is manual** (POST endpoint), not a scheduled poller — easier demo control
- **NVD rate limiting**: 6s delay between requests without API key, 0.6s with key
- **OSV enrichment**: Batch-only for specific packages in request body. Per-CVE enrichment was removed (caused 100+ blocking 400 errors for recent CVEs not yet in OSV).
- **Dedup**: By `cve_id`. Existing records are updated (packages, scores) but `vuln.discovered` is NOT re-published for existing CVEs.
- **Events collection**: Every published event is also stored in MongoDB `events` collection for `GET /events` visibility.
- **api_gateway proxy timeout**: 300s — NVD can be slow for large date ranges.
- **logger.propagate = False**: Added to shared logger to prevent double-output via uvicorn's root handler.
- **NVD API key**: Goes in `.env` only (gitignored). `.env.example` has empty `NVD_API_KEY=` placeholder.

---

## Merge conflict resolution (with Dev B / Thejas)

Dev B (Thejas) had committed Phases 4+5 (remediation_engine, gitlab_integration, api_gateway proxy routes). After a failed `git rebase`, our commit was dropped. Recovery steps:

1. `git reflog --oneline` — found dropped commit hash `83593a4`
2. `git cherry-pick 83593a4` — re-applied on top of Thejas's commits
3. Resolved conflict in `api_gateway/config.py` (kept all three service URLs)
4. `git cherry-pick --continue`
5. Final commit: `e02603b` "Dev A Phase 2 Part 1"

Current branch is `main` with both Dev A and Dev B work merged.

---

## Coordination item with Thejas (Dev B)

Thejas's `patch_generator.py` reads `repositories.seed_manifests[<path>]` from the repo MongoDB document during demo runs (to avoid needing real GitLab API calls). Our `seed_demo.py` does not yet populate this field.

**DONE**: `seed_manifests` added to all three repos in `scripts/seed_demo.py`:
- `repo-demo-001` (Java): `{"pom.xml": "...log4j-core 2.14.1..."}` — pom.xml patcher not yet implemented in remediation_engine; patch flow will fail at `_apply_manifest_patch("maven", ...)` until Thejas adds Maven support
- `repo-demo-002` (Python): `{"requirements.txt": "cryptography==38.0.0\nrequests==2.27.0\nFlask==2.0.0\nPyJWT==2.4.0\n"}`
- `repo-demo-003` (Python): `{"requirements.txt": "Pillow==9.0.0\nPyYAML==5.4.1\nrequests==2.26.0\nDjango==3.2.0\n"}`

Re-run `make seed-demo` to apply these to MongoDB.

---

## Next session

1. Set up GitLab demo repos with vulnerable dependency files
2. Implement repository matching (`vuln_intelligence/services/repo_matcher.py`)
3. Add dependency file parser for `requirements.txt`, `pom.xml`, `package.json`
4. Publish `vuln.matched` after matching
5. Wire up Vulnerabilities frontend page
