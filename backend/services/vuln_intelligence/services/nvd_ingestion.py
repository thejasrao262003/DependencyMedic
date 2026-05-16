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

    async def fetch_recent_cves(
        self,
        days_back: int = 30,
        severities: list[str] | None = None,
    ) -> list[dict]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days_back)

        base_params = {
            "pubStartDate": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate": end.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "noRejected": "",
            "resultsPerPage": 100,
        }
        headers = {"apiKey": self.api_key} if self.api_key else {}
        target_severities = [s.upper() for s in (severities or ["CRITICAL", "HIGH"])]

        all_vulns: list[dict] = []
        for severity in target_severities:
            await asyncio.sleep(self._request_delay)
            try:
                params = {**base_params, "cvssV3Severity": severity}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.get(NVD_BASE_URL, params=params, headers=headers)
                    r.raise_for_status()
                    data = r.json()

                items = data.get("vulnerabilities", [])
                for item in items:
                    normalized = self._normalize(item["cve"], severity.lower())
                    if normalized:
                        all_vulns.append(normalized)

                logger.info(
                    "NVD fetch complete",
                    extra={"severity": severity, "count": len(items)},
                )
            except Exception as exc:
                logger.error(
                    "NVD fetch failed",
                    extra={"severity": severity, "error": str(exc)},
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
