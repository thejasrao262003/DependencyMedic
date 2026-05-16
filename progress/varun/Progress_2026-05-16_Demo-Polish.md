# Session: Demo Polish — Gemini Fix, Frontend Redesign, Detail Page

**Date:** 2026-05-16
**Developer:** Varun (Dev A — Threat Intelligence)
**Status:** Dev A complete. Full end-to-end pipeline verified working.

---

## What was done this session

### Bug fixes

| File | Fix |
|------|-----|
| `reachability_analysis/agents/reachability_agent.py` | `gemini-1.5-flash` → `gemini-2.0-flash` (matches Thejas's ci_failure_agent) |
| `vuln_intelligence/services/nvd_ingestion.py` | NVD API v2 has a 120-day max date range — now chunks requests into 119-day windows. Added `verify=False` for corporate proxy SSL |
| `vuln_intelligence/services/osv_ingestion.py` | Added `verify=False` to both httpx clients for corporate proxy SSL |
| `docker-compose.yml` | Remapped all host ports to 9xxx range (existing ports were in use). Internal container ports unchanged — services still communicate on original ports |

**Port mapping (host → container):**
- api_gateway: `9000:8000`
- vuln_intelligence: `9001:8001`
- reachability_analysis: `9002:8002`
- remediation_engine: `9003:8003`
- gitlab_integration: `9004:8004`
- frontend: `9005:3000`
- mongodb: `27117:27017`
- redis: `6399:6379`

### New: `/match` endpoint for demo triggering

**Problem:** After `make seed-demo`, the seeded CVEs are already in the DB. Running ingest returns `new_stored: 0` so no events fire.

**Solution:** Added `POST /api/v1/vulnerabilities/{id}/match` — re-runs repo matching for any existing vuln and publishes `vuln.matched` regardless of whether it's new.

| File | Change |
|------|--------|
| `vuln_intelligence/api/ingest.py` | Added `POST /match/{vuln_id}` endpoint |
| `api_gateway/routes/vulnerabilities.py` | Proxy: `POST /vulnerabilities/{id}/match` |

**Demo trigger command:**
```bash
curl -s -X POST http://localhost:9000/api/v1/vulnerabilities/vuln-demo-003/match | python3 -m json.tool
```

### New: `make demo` command

Single command for a full clean demo run:
```bash
make demo
```

Does: `docker-compose down -v` → `make up` (wait 20s) → `make seed-demo` → trigger `/match` for `vuln-demo-003`.

### New: Python demo CVE in seed_demo.py

Added `vuln-demo-003` (CVE-2023-32681, requests SSRF, PyPI):
- `affected_packages: [{name: "requests", ecosystem: "pypi", fixed_versions: ["2.31.0"]}]`
- Matches `repo-demo-002` (requests==2.27.0) and `repo-demo-003` (requests==2.26.0)
- Python/PyPI → fully supported by Thejas's `manifest_patcher.py`
- This is the PRIMARY demo CVE for end-to-end flow

### Frontend: Full space-themed redesign

**Files changed:**
- `tailwind.config.js` — Space color palette, custom shadows, Inter + JetBrains Mono fonts
- `src/index.css` — CSS star field (20 radial-gradient dots), nebula glow, card/badge/button utility classes
- `src/App.tsx` — Left sidebar nav with icon labels, replaced top nav
- `src/pages/DashboardPage.tsx` — Mission Control header, stat cards, pipeline story flow, service health grid
- `src/pages/VulnerabilitiesPage.tsx` — Clickable rows (navigate to detail), ingest result with matched_published count
- `src/pages/RepositoriesPage.tsx` — Language badges, pulsing status dot, clean layout
- `src/pages/RemediationsPage.tsx` — Expandable dep-change details, status filter, auto-refresh
- `src/pages/PipelinesPage.tsx` — Duration display, failure detail with log box, auto-refresh
- `src/pages/MergeRequestsPage.tsx` — Approve button, GitLab link, status filter
- `src/types/index.ts` — Added `references: string[]` to Vulnerability interface

**New file:**
- `src/pages/VulnerabilityDetailPage.tsx` — Full CVE detail view:
  - Severity-colored glow header with CVSS + EPSS score cards
  - Affected packages table (name, ecosystem, affected range, fix version)
  - "Trigger Remediation Pipeline" button — calls `/match`, shows matched repos inline
  - Links to Remediations → Pipelines → MRs to follow the journey
  - References list
  - Route: `/vulnerabilities/:id`

---

## End-to-end demo verified working

**Full chain confirmed in logs:**
```
POST /api/v1/vulnerabilities/vuln-demo-003/match
  → vuln.matched (repo-demo-002, repo-demo-003)
    → reachability_analysis: risk_score=96, critical, confidence=0.95
      → vuln.assessed + vuln.scored published
        → remediation_engine: requests 2.27.0→2.31.0 and 2.26.0→2.31.0
          → gitlab_integration (mock mode):
              attempt-1: pipeline FAILED (unit_tests) → ci.failed emitted
              CI failure agent → retry requested
              attempt-2: pipeline PASSED → patch.validated
              → MR created x2
```

Total time from trigger to MR: ~70 seconds with mock GitLab.

**To run the demo:**
1. `make demo` — full clean run (takes ~2 min for startup)
2. OR if stack already up: `make seed-demo && curl -s -X POST http://localhost:9000/api/v1/vulnerabilities/vuln-demo-003/match`
3. Frontend: http://localhost:9005
4. API docs: http://localhost:9000/docs

---

## Dev A status: COMPLETE

All phases done:
- **Phase 1** ✅ — Infrastructure, shared contracts, service skeletons
- **Phase 2** ✅ — NVD/OSV ingestion, repo matching, `vuln.discovered` + `vuln.matched`
- **Phase 3** ✅ — `reachability_analysis` service, `vuln.assessed` + `vuln.scored`
- **Frontend** ✅ — All pages, space theme, vuln detail page with pipeline trigger

---

## Notes for Thejas (Dev B)

1. **GITLAB_TOKEN must be empty** in `.env` for the mock client to activate. If set (even to a real token), gitlab_integration will try to hit real GitLab → SSL errors on corporate network.

2. **Demo CVE** is `vuln-demo-003` (CVE-2023-32681, `requests`, PyPI). The log4j vulns (`vuln-demo-001`, `vuln-demo-002`) match `repo-demo-001` (Java) but Maven patching is not implemented in `manifest_patcher.py` — patch generation will fail at `_apply_manifest_patch("maven", ...)`. Stick to Python repos for the demo.

3. **Port mapping changed** — all host ports are in 9xxx range now. Internal Docker networking unchanged.

4. **`/match` endpoint** is the demo entry point. Call it with any vuln_id that has `affected_packages` populated.

5. **Gemini model** is now `gemini-2.0-flash` in both services (reachability_agent + ci_failure_agent). If `GEMINI_API_KEY` is set, both agents will produce LLM-enriched summaries. Falls back to deterministic if key is missing or API fails.
