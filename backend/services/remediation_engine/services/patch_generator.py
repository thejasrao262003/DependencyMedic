"""Patch generation orchestration.

Given a vulnerability_id + repository_id (typically arriving via vuln.scored),
produce a patch_attempt document and emit patch.generated. The actual file
changes (manifest text + path) are passed forward in the event payload so that
gitlab_integration can commit them — remediation_engine never touches GitLab
directly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from shared.constants import (
    COLLECTION_DEPENDENCY_SNAPSHOTS,
    COLLECTION_PATCH_ATTEMPTS,
    COLLECTION_REPOSITORIES,
    COLLECTION_VULNERABILITIES,
)
from shared.enums import PatchStatus
from shared.events.base import BaseEvent
from shared.events.patch_events import DependencyChange, PatchGeneratedPayload
from shared.logging import get_logger
from shared.utils.mongo import get_database
from shared.utils.redis_streams import RedisStreamPublisher
from shared.utils.version import choose_fix_version

from ..patchers.manifest_patcher import (
    patch_package_json,
    patch_requirements_txt,
)

logger = get_logger("remediation_engine.patch_generator")


class PatchGenerationError(Exception):
    """Raised when a patch cannot be generated deterministically."""


async def generate_patch(
    repository_id: str,
    vulnerability_id: str,
    correlation_id: str,
    publisher: RedisStreamPublisher,
    *,
    attempt_number: int = 1,
    retry_reason: str | None = None,
) -> str:
    """Run the deterministic patch flow and emit patch.generated. Returns patch_attempt_id.

    Raises PatchGenerationError when no actionable patch can be produced — the
    caller is responsible for logging escalation.
    """
    db = get_database()

    repo = await db[COLLECTION_REPOSITORIES].find_one({"_id": repository_id})
    if not repo:
        raise PatchGenerationError(f"repository {repository_id} not found")

    vuln = await db[COLLECTION_VULNERABILITIES].find_one({"_id": vulnerability_id})
    if not vuln:
        raise PatchGenerationError(f"vulnerability {vulnerability_id} not found")

    affected = vuln.get("affected_packages") or []
    if not affected:
        raise PatchGenerationError("vulnerability has no affected_packages")
    pkg = affected[0]
    pkg_name = pkg.get("name")
    ecosystem = (pkg.get("ecosystem") or "").lower()
    fixed_versions = pkg.get("fixed_versions") or []

    snapshot = await db[COLLECTION_DEPENDENCY_SNAPSHOTS].find_one(
        {"repository_id": repository_id},
        sort=[("generated_at", -1)],
    )
    installed_version = "0"
    manifest_path = _default_manifest_path(ecosystem)
    if snapshot:
        for dep in snapshot.get("dependencies", []) or []:
            if dep.get("name") == pkg_name:
                installed_version = dep.get("version") or "0"
                manifest_path = dep.get("manifest_path") or manifest_path
                break

    fix_version = choose_fix_version(installed_version, fixed_versions)
    if not fix_version:
        raise PatchGenerationError(
            f"no upgrade path: installed={installed_version}, fixes={fixed_versions}"
        )

    manifest_text = _load_seeded_manifest(repo, manifest_path)
    patched_text, from_version = _apply_manifest_patch(
        ecosystem, manifest_text, pkg_name, fix_version
    )
    if from_version is None:
        raise PatchGenerationError(
            f"package {pkg_name} not found in manifest {manifest_path}"
        )

    cve_id = vuln.get("cve_id", vulnerability_id)
    patch_attempt_id = str(uuid.uuid4())
    branch_name = f"fix/{cve_id.lower()}-attempt-{attempt_number}"
    now = datetime.now(timezone.utc)

    doc = {
        "_id": patch_attempt_id,
        "repository_id": repository_id,
        "vulnerability_id": vulnerability_id,
        "branch_name": branch_name,
        "manifest_path": manifest_path,
        "manifest_content": patched_text,
        "dependency_changes": [
            {"package": pkg_name, "from_version": from_version, "to_version": fix_version}
        ],
        "attempt_number": attempt_number,
        "status": PatchStatus.GENERATED.value,
        "llm_used": False,
        "confidence_score": 0.95,
        "retry_reason": retry_reason,
        "patch_summary": (
            f"Bump {pkg_name} from {from_version} to {fix_version} to address {cve_id}"
        ),
        "correlation_id": correlation_id,
        "created_at": now,
        "updated_at": now,
        "created_by": "remediation_engine",
        "version": 1,
    }
    await db[COLLECTION_PATCH_ATTEMPTS].insert_one(doc)

    payload = PatchGeneratedPayload(
        patch_attempt_id=patch_attempt_id,
        repository_id=repository_id,
        vulnerability_id=vulnerability_id,
        branch_name=branch_name,
        dependency_changes=[
            DependencyChange(
                package=pkg_name, from_version=from_version, to_version=fix_version
            )
        ],
        attempt_number=attempt_number,
    )
    event = BaseEvent(
        event_type="patch.generated",
        source_service="remediation_engine",
        correlation_id=correlation_id,
        payload=payload.model_dump(),
    )
    await publisher.publish(event)
    logger.info(
        "Patch generated",
        extra={
            "patch_attempt_id": patch_attempt_id,
            "repository_id": repository_id,
            "vulnerability_id": vulnerability_id,
            "package": pkg_name,
            "from_version": from_version,
            "to_version": fix_version,
            "attempt_number": attempt_number,
            "correlation_id": correlation_id,
        },
    )
    return patch_attempt_id


def _default_manifest_path(ecosystem: str) -> str:
    if ecosystem in ("pypi", "python"):
        return "requirements.txt"
    if ecosystem in ("npm", "node"):
        return "package.json"
    return "requirements.txt"


def _apply_manifest_patch(
    ecosystem: str, manifest_text: str, package: str, to_version: str
) -> tuple[str, str | None]:
    if ecosystem in ("pypi", "python"):
        return patch_requirements_txt(manifest_text, package, to_version)
    if ecosystem in ("npm", "node"):
        return patch_package_json(manifest_text, package, to_version)
    raise PatchGenerationError(f"unsupported ecosystem: {ecosystem}")


def _load_seeded_manifest(repo: dict, manifest_path: str) -> str:
    """Return the seeded manifest content for a demo repo.

    Real GitLab integration will fetch this via the GitLab Files API; for the
    MVP demo we keep a deterministic seed under repositories.seed_manifests so
    the patch flow is reproducible without network access.
    """
    seed = (repo.get("seed_manifests") or {}).get(manifest_path)
    if seed is None:
        raise PatchGenerationError(
            f"no seed_manifests[{manifest_path}] on repository {repo.get('_id')}"
        )
    return seed
