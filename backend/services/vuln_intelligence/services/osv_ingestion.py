import httpx

from shared.logging import get_logger

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"

logger = get_logger("vuln_intelligence.osv")

_SEVERITY_MAP = {"critical", "high", "medium", "low"}


class OSVIngestionService:
    async def enrich_with_packages(self, cve_id: str) -> list[dict]:
        """Query OSV by CVE ID and return affected package list."""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.post(OSV_QUERY_URL, json={"id": cve_id})
                if r.status_code == 404:
                    return []
                r.raise_for_status()
                data = r.json()

            packages: list[dict] = []
            for vuln in data.get("vulns", []):
                for affected in vuln.get("affected", []):
                    pkg = affected.get("package", {})
                    name = pkg.get("name", "")
                    if not name:
                        continue
                    fixed_versions = self._extract_fixed_versions(affected.get("ranges", []))
                    affected_range = self._extract_version_range(affected.get("ranges", []))
                    packages.append({
                        "name": name,
                        "ecosystem": pkg.get("ecosystem", ""),
                        "affected_versions": affected_range,
                        "fixed_versions": fixed_versions[:5],
                    })
            return packages
        except Exception as exc:
            logger.warning(
                "OSV enrichment skipped",
                extra={"cve_id": cve_id, "error": str(exc)},
            )
            return []

    async def fetch_vulns_for_packages(self, packages: list[dict]) -> list[dict]:
        """Batch query OSV for vulnerabilities affecting the given packages."""
        if not packages:
            return []
        try:
            queries = [
                {"package": {"name": p["name"], "ecosystem": p["ecosystem"]}}
                for p in packages
            ]
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(OSV_BATCH_URL, json={"queries": queries})
                r.raise_for_status()
                data = r.json()

            results: list[dict] = []
            for i, result in enumerate(data.get("results", [])):
                source_pkg = packages[i] if i < len(packages) else {}
                for vuln in result.get("vulns", []):
                    normalized = self._normalize_osv_vuln(vuln, source_pkg)
                    if normalized:
                        results.append(normalized)
            return results
        except Exception as exc:
            logger.error("OSV batch fetch failed", extra={"error": str(exc)})
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_fixed_versions(self, ranges: list) -> list[str]:
        fixed: list[str] = []
        for rng in ranges:
            for event in rng.get("events", []):
                if "fixed" in event:
                    fixed.append(event["fixed"])
        return fixed

    def _extract_version_range(self, ranges: list) -> str:
        parts: list[str] = []
        for rng in ranges:
            for event in rng.get("events", []):
                if "introduced" in event:
                    parts.append(f">={event['introduced']}")
                if "fixed" in event:
                    parts.append(f"<{event['fixed']}")
        return ", ".join(parts) if parts else "unknown"

    def _safe_severity(self, vuln: dict) -> str:
        db_specific = vuln.get("database_specific", {})
        raw = db_specific.get("severity", "")
        if raw and raw.lower() in _SEVERITY_MAP:
            return raw.lower()
        return "medium"

    def _normalize_osv_vuln(self, vuln: dict, source_pkg: dict) -> dict | None:
        vuln_id = vuln.get("id", "")
        if not vuln_id:
            return None

        # Prefer CVE ID as primary identifier
        cve_id = vuln_id
        aliases: list[str] = []
        for alias in vuln.get("aliases", []):
            if alias.startswith("CVE-") and cve_id == vuln_id:
                cve_id = alias
            else:
                aliases.append(alias)

        summary = vuln.get("summary", "") or vuln.get("details", "")
        summary = summary[:200] if summary else f"Vulnerability {cve_id}"

        affected_packages: list[dict] = []
        for affected in vuln.get("affected", []):
            pkg = affected.get("package", {})
            name = pkg.get("name", "")
            if not name:
                continue
            fixed_versions = self._extract_fixed_versions(affected.get("ranges", []))
            affected_packages.append({
                "name": name,
                "ecosystem": pkg.get("ecosystem", ""),
                "affected_versions": self._extract_version_range(affected.get("ranges", [])),
                "fixed_versions": fixed_versions[:5],
            })

        references = [
            r["url"] for r in vuln.get("references", []) if r.get("url")
        ]

        return {
            "cve_id": cve_id,
            "aliases": [vuln_id] + aliases if cve_id != vuln_id else aliases,
            "summary": summary,
            "description": vuln.get("details", ""),
            "severity": self._safe_severity(vuln),
            "cvss_score": None,
            "epss_score": None,
            "published_at": vuln.get("published"),
            "affected_packages": affected_packages,
            "references": references[:10],
            "source": "OSV",
        }
