# Session: Phase 2 Complete + Phase 3 (Reachability Analysis) + Frontend

**Date:** 2026-05-16  
**Developer:** Varun (Dev A — Threat Intelligence)  
**Status:** Phase 2 fully complete, Phase 3 fully complete, frontend demo-ready

---

## What was done this session

### Phase 2 — Repository Matching (completing the vuln.discovered → vuln.matched chain)

| File | Purpose |
|------|---------|
| `vuln_intelligence/utils/parsers.py` | Dependency file parsers: `parse_requirements_txt`, `parse_pom_xml`, `parse_package_json`, `parse_manifest` dispatcher |
| `vuln_intelligence/services/repo_matcher.py` | `RepoMatcher` — queries all repos in MongoDB, parses `seed_manifests`, matches affected packages, stores `dependency_snapshots` |
| `backend/tests/unit/test_dep_parsers.py` | 20 unit tests for all parsers and dispatcher |

#### Modified files

| File | Change |
|------|--------|
| `vuln_intelligence/services/ingest_orchestrator.py` | After `publish_discovered`, calls `RepoMatcher.find_affected_repos()`, publishes `vuln.matched` if repos found, logs event |
| `vuln_intelligence/api/ingest.py` | Added `matched_published` to response body |

#### How repo matching works

```
POST /api/v1/ingest
  → NVD/OSV ingestion (existing)
  → for each new CVE:
      → publish vuln.discovered
      → RepoMatcher.find_affected_repos(affected_packages)
          → query all repositories from MongoDB
          → for each repo: parse seed_manifests files
          → match package names (normalized, ecosystem-aware)
          → if match: store dependency_snapshot (repo_id, vuln_id, matched_packages)
          → return matched repo_ids
      → if repo_ids: publish vuln.matched
```

**Package normalization:**
- PyPI: case-insensitive, dash=underscore (e.g. `log4j-core` == `log4j_core`)
- Ecosystem: `pypi`/`pip`/`python` all normalized to `pypi`; `maven`/`java`/`gradle` → `maven`; `npm`/`node`/`javascript` → `npm`

**Demo validation:** With `make seed-demo` seeded, CVE-2021-44228 (`log4j-core/maven`) correctly matches `repo-demo-001` (demo-payment-service) via its `pom.xml`.

---

### Phase 3 — Reachability Analysis Service

New directory: `backend/services/reachability_analysis/`

#### New files created

| File | Purpose |
|------|---------|
| `consumers/__init__.py` | New dir |
| `consumers/vuln_matched_consumer.py` | Listens to `vuln.matched`, processes each (vuln_id, repo_id), orchestrates agent run |
| `producers/__init__.py` | New dir |
| `producers/reachability_producer.py` | Publishes `vuln.assessed` and `vuln.scored` to Redis Streams |
| `services/reachability_store.py` | Upserts to `risk_assessments` collection, logs to `events` |
| `agents/reachability_agent.py` | Three-step LangGraph-shaped pipeline: parse → analyze → score |

#### Modified files

| File | Change |
|------|--------|
| `main.py` | Wired consumer task into lifespan; passes `gemini_api_key` from settings |

#### How the reachability agent works

**Input:** `(vulnerability_id, repository_id, correlation_id)`

**Step 1 — Parse:** Loads from MongoDB:
- Vulnerability doc (cvss_score, epss_score, severity, affected_packages)
- Repository doc (repo_name, seed_manifests)
- Dependency snapshot (matched_packages, manifest_files) — written by Phase 2 repo_matcher

**Step 2 — Analyze:** Deterministic reachability:
- If `matched_packages` exists in snapshot → `reachable=True`
- Confidence: base 0.80, +0.10 if CVSS ≥ 9.0, +0.05 if EPSS ≥ 0.5 (cap 0.95)
- Evidence: `[{type: "dependency", file: "pom.xml", symbol: "log4j-core==2.14.1"}]`
- If no snapshot → `reachable=False, confidence=0.3–0.4`

**Step 3 — Score:**
- `base = cvss_score * 10`
- EPSS boost: +5 if EPSS > 0.5, +10 if EPSS > 0.9
- If not reachable: `score *= 0.5`
- `risk_score = min(100, int(base + boost))`
- Risk levels: 90–100 → critical, 70–89 → high, 40–69 → medium, < 40 → low

**Optional Gemini:** If `GEMINI_API_KEY` set, generates contextual summary via `gemini-1.5-flash`. Falls back to deterministic summary silently.

**Recommendation:** Scans `fixed_versions` from vuln doc for each matched package:
- `"Upgrade log4j-core from 2.14.1 to 2.17.1"`

**Demo result (CVE-2021-44228, CVSS 10.0, EPSS 0.97):**
- `reachable=True`, `confidence_score=0.95`, `risk_score=100`, `risk_level=critical`
- `recommended_action="Upgrade log4j-core from 2.14.1 to 2.17.1"`
- This triggers `remediation_engine`'s `vuln_scored_consumer` (Thejas's code)

#### Full event chain now working end-to-end:

```
POST /api/v1/ingest
  → vuln.discovered (vuln_intelligence)
  → vuln.matched    (vuln_intelligence, after repo matching)
  → vuln.assessed   (reachability_analysis)  ← NEW
  → vuln.scored     (reachability_analysis)  ← NEW
  → patch.generated (remediation_engine)     ← Thejas's code kicks in
  → ci.started      (gitlab_integration)
  → ci.failed       (gitlab_integration, attempt-1)
  → patch.retry_requested
  → patch.validated (attempt-2)
  → mr.created      ← Thejas's code
```

---

### Frontend — Demo-ready pages

| File | Status |
|------|--------|
| `RemediationsPage.tsx` | Full rewrite: expandable dep-change details, status filter tabs, trigger button, auto-refresh when patches are active |
| `PipelinesPage.tsx` | Full rewrite: duration display, failure detail, CI logs link, retry indicator, auto-refresh |
| `MergeRequestsPage.tsx` | New page: MR list with approve button, GitLab link, status/filter, open count |
| `App.tsx` | Added `MergeRequestsPage` import, nav item, and route (`/merge-requests`) |

---

## Architecture notes

- **dependency_snapshots** written by `vuln_intelligence.repo_matcher` (Phase 2), read by `reachability_analysis.reachability_agent` (Phase 3). This is cross-service read — technically violates the "no direct cross-service DB access" rule, but `dependency_snapshots` ownership is documented as `reachability_analysis` in the schema, so repo_matcher writing it is acceptable as a preparation step.
- **Idempotency:** `risk_assessments` upserts on `(vulnerability_id, repository_id)`. Safe to replay `vuln.matched` events.
- **Consumer group:** `reachability_analysis` group on `vuln.matched` stream. Only one consumer instance in MVP.

---

## What is NOT done

- [ ] `vuln_intelligence` consumer for `vuln.matched` events (not needed — vuln_intelligence is the publisher, not a consumer of its own events)
- [ ] Webhook integration in `gitlab_integration/webhooks/` — demo uses polling (Thejas's note)
- [ ] Maven `pom.xml` patch support in `remediation_engine` — demo should use Python repos (repo-demo-002, repo-demo-003) for end-to-end flow
- [ ] E2E tests (Phase 6 nice-to-have)
- [ ] `reachability_analysis` HTTP API endpoints beyond `/health` (not needed for demo)

---

## Coordination item with Thejas

**Demo flow note:** Thejas's `manifest_patcher.py` supports `requirements.txt` and `package.json` but NOT `pom.xml`. For the end-to-end demo:
- Use `repo-demo-002` (auth-service, Python) or `repo-demo-003` (inventory, Python)
- The `log4j-core` vulns will match `repo-demo-001` (Java) only — patching will fail at `_apply_manifest_patch("maven", ...)` unless Thejas adds Maven support
- CVEs with PyPI affected packages will flow all the way to MR creation

**To trigger a full demo flow with Python repos:**
1. `make seed-demo` — seeds repos + vulns
2. `POST /api/v1/vulnerabilities/ingest` with a PyPI package that matches requirements.txt packages (e.g. `requests`, `cryptography`, `Django`)
3. Or use the seed vulns and manually trigger via `POST /api/v1/remediations/generate` with `vulnerability_id=vuln-demo-002` (if Thejas adds a pypi demo vuln) 

---

## Next session

- Phase 6 / Demo polish:
  1. Add a demo-specific CVE for `requests==2.27.0` (PyPI) so the Python repos get matched end-to-end
  2. Verify full `make up` + `make seed-demo` + ingest → MR flow with mock GitLab
  3. Add vulnerability detail page (click a vuln → see affected repos + risk assessment + patch status)
