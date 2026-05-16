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
| `api_gateway/config.py` | Added `vuln_intelligence_url = http://vuln_intelligence:8001` |
| `api_gateway/routes/vulnerabilities.py` | Added `POST /vulnerabilities/ingest` proxy to vuln_intelligence |
| `.env.example` | Added `NVD_API_KEY` |

---

## How the ingestion works

```
POST /api/v1/vulnerabilities/ingest (api_gateway:8000)
  → proxies to POST /api/v1/ingest (vuln_intelligence:8001)
    → NVDIngestionService.fetch_recent_cves(days_back, severities)
    → OSVIngestionService.fetch_vulns_for_packages(extra_packages)  [optional]
    → per CVE: OSVIngestionService.enrich_with_packages(cve_id)
    → VulnStore.upsert_vulnerability(vuln_dict) → (vuln_id, is_new)
    → if is_new: VulnProducer.publish_discovered(...)  → Redis stream "vuln.discovered"
    → if is_new: VulnStore.log_event(...)               → MongoDB "events" collection
```

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
- [ ] Frontend: populated Vulnerabilities page (table with real data)
- [ ] GitLab repos set up with vulnerable dependency files (Varun doing manually)

---

## Key decisions made

- **Trigger is manual** (POST endpoint), not a scheduled poller — easier demo control
- **NVD rate limiting**: 6s delay between requests without API key, 0.6s with key
- **OSV enrichment**: Called per-CVE after NVD fetch to get package data. OSV batch used for package-specific queries.
- **Dedup**: By `cve_id`. Existing records are updated (packages, scores) but `vuln.discovered` is NOT re-published for existing CVEs.
- **Events collection**: Every published event is also stored in MongoDB `events` collection for `GET /events` visibility.
- **api_gateway proxy timeout**: 300s — NVD can be slow for large date ranges.

---

## Next session

1. Set up GitLab demo repos with vulnerable dependency files
2. Implement repository matching (`vuln_intelligence/services/repo_matcher.py`)
3. Add dependency file parser for `requirements.txt`, `pom.xml`, `package.json`
4. Publish `vuln.matched` after matching
5. Wire up Vulnerabilities frontend page
