import asyncio
from datetime import datetime, timezone, timedelta
import httpx

from shared.logging import get_logger

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

logger = get_logger("vuln_intelligence.nvd")

_SEVERITY_MAP = {"critical", "high", "medium", "low"}


class NVDIngestionService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or None
        # NVD rate limits: 5 req/30s without key, 50 req/30s with key
        self._request_delay = 0.6 if self.api_key else 6.0

    # NVD API v2 enforces a 120-day maximum date range per request
    _NVD_MAX_WINDOW_DAYS = 119

    async def fetch_recent_cves(
        self,
        days_back: int = 30,
        severities: list[str] | None = None,
    ) -> list[dict]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days_back)
        headers = {"apiKey": self.api_key} if self.api_key else {}
        target_severities = [s.upper() for s in (severities or ["CRITICAL", "HIGH"])]

        # Chunk the date range into <=119-day windows to stay within NVD's limit
        windows: list[tuple[datetime, datetime]] = []
        window_start = start
        while window_start < end:
            window_end = min(window_start + timedelta(days=self._NVD_MAX_WINDOW_DAYS), end)
            windows.append((window_start, window_end))
            window_start = window_end

        all_vulns: list[dict] = []
        seen_ids: set[str] = set()

        for severity in target_severities:
            for w_start, w_end in windows:
                await asyncio.sleep(self._request_delay)
                try:
                    params = {
                        "pubStartDate": w_start.strftime("%Y-%m-%dT%H:%M:%S.000"),
                        "pubEndDate": w_end.strftime("%Y-%m-%dT%H:%M:%S.000"),
                        "noRejected": "",
                        "resultsPerPage": 100,
                        "cvssV3Severity": severity,
                    }
                    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                        r = await client.get(NVD_BASE_URL, params=params, headers=headers)
                        r.raise_for_status()
                        data = r.json()

                    items = data.get("vulnerabilities", [])
                    new_count = 0
                    for item in items:
                        normalized = self._normalize(item["cve"], severity.lower())
                        if normalized and normalized["cve_id"] not in seen_ids:
                            seen_ids.add(normalized["cve_id"])
                            all_vulns.append(normalized)
                            new_count += 1

                    logger.info(
                        "NVD fetch complete",
                        extra={
                            "severity": severity,
                            "window_start": w_start.date().isoformat(),
                            "window_end": w_end.date().isoformat(),
                            "count": new_count,
                        },
                    )
                except Exception as exc:
                    logger.error(
                        "NVD fetch failed",
                        extra={
                            "severity": severity,
                            "window_start": w_start.date().isoformat(),
                            "error": str(exc),
                        },
                    )

        return all_vulns

    def _normalize(self, cve: dict, severity: str) -> dict | None:
        cve_id = cve.get("id", "")
        if not cve_id:
            return None

        descriptions = cve.get("descriptions", [])
        en_desc = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")

        cvss_score: float | None = None
        metrics = cve.get("metrics", {})
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            metric_list = metrics.get(key, [])
            if metric_list:
                cvss_score = metric_list[0].get("cvssData", {}).get("baseScore")
                break

        references = [r["url"] for r in cve.get("references", []) if "url" in r]

        published_at: str | None = None
        raw_pub = cve.get("published")
        if raw_pub:
            try:
                published_at = datetime.fromisoformat(
                    raw_pub.replace("Z", "+00:00")
                ).isoformat()
            except Exception:
                pass

        safe_severity = severity if severity in _SEVERITY_MAP else "medium"

        return {
            "cve_id": cve_id,
            "aliases": [],
            "summary": (en_desc[:200] if en_desc else f"Vulnerability {cve_id}"),
            "description": en_desc,
            "severity": safe_severity,
            "cvss_score": cvss_score,
            "epss_score": None,
            "published_at": published_at,
            "affected_packages": [],
            "references": references[:10],
            "source": "NVD",
        }
