"""Repository matcher: finds repos whose deps overlap a CVE's affected packages."""
import uuid
from datetime import datetime, timezone

from shared.utils.mongo import get_database
from shared.constants import COLLECTION_REPOSITORIES, COLLECTION_DEPENDENCY_SNAPSHOTS
from shared.logging import get_logger
from ..utils.parsers import parse_manifest, Dependency

logger = get_logger("vuln_intelligence.repo_matcher")

# Normalize ecosystem names so "PyPI" == "pypi" == "pip", etc.
_ECOSYSTEM_ALIASES: dict[str, set[str]] = {
    "pypi": {"pypi", "pip", "python"},
    "maven": {"maven", "java", "gradle"},
    "npm": {"npm", "node", "javascript", "nodejs"},
}


def _normalize_ecosystem(eco: str) -> str:
    eco_lower = eco.lower()
    for canonical, aliases in _ECOSYSTEM_ALIASES.items():
        if eco_lower in aliases:
            return canonical
    return eco_lower


def _normalize_pkg_name(name: str, ecosystem: str) -> str:
    """Normalize package name for comparison (PyPI is case-insensitive, dashes==underscores)."""
    name = name.lower()
    if ecosystem == "pypi":
        name = name.replace("-", "_")
    return name


class RepoMatcher:
    async def find_affected_repos(
        self,
        affected_packages: list[dict],
        vuln_id: str,
        correlation_id: str,
    ) -> list[str]:
        """
        Given a CVE's affected_packages list, scan all registered repositories and
        return the IDs of those whose dependency manifests contain any of the packages.

        Also persists a dependency_snapshot for each matched repo so that
        reachability_analysis can build its call graph without re-parsing.
        """
        if not affected_packages:
            return []

        # Build lookup: {(normalized_name, normalized_ecosystem)}
        targets: set[tuple[str, str]] = set()
        for pkg in affected_packages:
            raw_name = pkg.get("name", "").strip()
            eco = _normalize_ecosystem(pkg.get("ecosystem", ""))
            if raw_name:
                targets.add((_normalize_pkg_name(raw_name, eco), eco))

        if not targets:
            return []

        db = get_database()
        repos = await db[COLLECTION_REPOSITORIES].find({}).to_list(length=None)

        matched_ids: list[str] = []

        for repo in repos:
            seed_manifests: dict = repo.get("seed_manifests", {})
            if not seed_manifests:
                continue

            # Parse all manifest files in this repo
            all_deps: list[Dependency] = []
            for filename, content in seed_manifests.items():
                all_deps.extend(parse_manifest(filename, content))

            # Check for any overlap with target packages
            matched_deps = [
                dep
                for dep in all_deps
                if (
                    _normalize_pkg_name(dep.name, _normalize_ecosystem(dep.ecosystem)),
                    _normalize_ecosystem(dep.ecosystem),
                )
                in targets
            ]

            if not matched_deps:
                continue

            repo_id = str(repo["_id"])
            matched_ids.append(repo_id)

            logger.info(
                "Repository matched to vulnerability",
                extra={
                    "repo_id": repo_id,
                    "repo_name": repo.get("repo_name"),
                    "matched_packages": [d.name for d in matched_deps],
                    "vuln_id": vuln_id,
                    "correlation_id": correlation_id,
                },
            )

            await self._store_dependency_snapshot(
                db=db,
                repo_id=repo_id,
                vuln_id=vuln_id,
                all_deps=all_deps,
                matched_deps=matched_deps,
                manifest_files=list(seed_manifests.keys()),
                correlation_id=correlation_id,
            )

        return matched_ids

    async def _store_dependency_snapshot(
        self,
        db,
        repo_id: str,
        vuln_id: str,
        all_deps: list[Dependency],
        matched_deps: list[Dependency],
        manifest_files: list[str],
        correlation_id: str,
    ) -> None:
        """
        Upsert a dependency_snapshot document for (repo_id, vuln_id).
        Reachability_analysis reads these snapshots to avoid re-parsing manifests.
        """
        now = datetime.now(timezone.utc).isoformat()
        snapshot_id = str(uuid.uuid4())

        await db[COLLECTION_DEPENDENCY_SNAPSHOTS].update_one(
            {"repo_id": repo_id, "vuln_id": vuln_id},
            {
                "$set": {
                    "repo_id": repo_id,
                    "vuln_id": vuln_id,
                    "correlation_id": correlation_id,
                    "manifest_files": manifest_files,
                    "total_dependencies": len(all_deps),
                    "matched_packages": [
                        {"name": d.name, "version": d.version, "ecosystem": d.ecosystem}
                        for d in matched_deps
                    ],
                    "all_dependencies": [
                        {"name": d.name, "version": d.version, "ecosystem": d.ecosystem}
                        for d in all_deps
                    ],
                    "updated_at": now,
                    "created_by": "vuln_intelligence",
                    "version": 1,
                },
                "$setOnInsert": {
                    "_id": snapshot_id,
                    "created_at": now,
                },
            },
            upsert=True,
        )
        logger.info(
            "Stored dependency snapshot",
            extra={
                "repo_id": repo_id,
                "vuln_id": vuln_id,
                "matched_count": len(matched_deps),
                "correlation_id": correlation_id,
            },
        )
