"""Open a remediation MR after a patch is validated."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from shared.constants import (
    COLLECTION_MERGE_REQUESTS,
    COLLECTION_PATCH_ATTEMPTS,
    COLLECTION_REPOSITORIES,
    COLLECTION_RISK_ASSESSMENTS,
    COLLECTION_VULNERABILITIES,
)
from shared.enums import MRStatus
from shared.events.base import BaseEvent
from shared.events.mr_events import MrCreatedPayload
from shared.logging import get_logger
from shared.utils.mongo import get_database
from shared.utils.redis_streams import RedisStreamPublisher

from ..clients.protocol import GitLabClient

logger = get_logger("gitlab_integration.mr_creator")

_DEFAULT_REVIEWERS = ["security-team"]


async def create_remediation_mr(
    *,
    client: GitLabClient,
    publisher: RedisStreamPublisher,
    patch_attempt_id: str,
    pipeline_run_id: str,
    correlation_id: str,
) -> None:
    db = get_database()
    patch = await db[COLLECTION_PATCH_ATTEMPTS].find_one({"_id": patch_attempt_id})
    if not patch:
        logger.warning(
            "mr_creator: patch_attempt missing",
            extra={"patch_attempt_id": patch_attempt_id, "correlation_id": correlation_id},
        )
        return
    repo = await db[COLLECTION_REPOSITORIES].find_one({"_id": patch["repository_id"]})
    if not repo:
        logger.warning(
            "mr_creator: repository missing",
            extra={"repository_id": patch["repository_id"], "correlation_id": correlation_id},
        )
        return
    vuln = await db[COLLECTION_VULNERABILITIES].find_one({"_id": patch["vulnerability_id"]})
    risk = await db[COLLECTION_RISK_ASSESSMENTS].find_one(
        {"vulnerability_id": patch["vulnerability_id"], "repository_id": patch["repository_id"]}
    )

    cve_id = (vuln or {}).get("cve_id", patch["vulnerability_id"])
    title = f"Fix {cve_id}: {patch.get('patch_summary') or 'dependency upgrade'}"
    description = _render_description(patch=patch, vuln=vuln, risk=risk, pipeline_run_id=pipeline_run_id)

    project_id = repo.get("gitlab_project_id") or repo["_id"]
    target_branch = repo.get("default_branch", "main")
    try:
        result = await client.create_merge_request(
            project_id=project_id,
            source_branch=patch["branch_name"],
            target_branch=target_branch,
            title=title,
            description=description,
            reviewers=_DEFAULT_REVIEWERS,
        )
    except Exception as err:  # noqa: BLE001
        logger.exception(
            "GitLab MR creation failed",
            extra={
                "patch_attempt_id": patch_attempt_id,
                "correlation_id": correlation_id,
                "error": str(err),
            },
        )
        return

    merge_request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await db[COLLECTION_MERGE_REQUESTS].insert_one(
        {
            "_id": merge_request_id,
            "repository_id": patch["repository_id"],
            "patch_attempt_id": patch_attempt_id,
            "gitlab_mr_id": result.iid,
            "title": title,
            "status": MRStatus.OPENED.value,
            "reviewers": _DEFAULT_REVIEWERS,
            "approval_required": True,
            "approved": False,
            "mergeable": True,
            "mr_url": result.web_url,
            "correlation_id": correlation_id,
            "created_at": now,
            "updated_at": now,
            "created_by": "gitlab_integration",
            "version": 1,
        }
    )
    await publisher.publish(
        BaseEvent(
            event_type="mr.created",
            source_service="gitlab_integration",
            correlation_id=correlation_id,
            payload=MrCreatedPayload(
                merge_request_id=merge_request_id,
                repository_id=patch["repository_id"],
                patch_attempt_id=patch_attempt_id,
                gitlab_mr_id=result.iid,
                title=title,
                mr_url=result.web_url,
                reviewers=_DEFAULT_REVIEWERS,
            ).model_dump(),
        )
    )
    logger.info(
        "Merge request opened",
        extra={
            "merge_request_id": merge_request_id,
            "patch_attempt_id": patch_attempt_id,
            "mr_url": result.web_url,
            "correlation_id": correlation_id,
        },
    )


def _render_description(*, patch: dict, vuln: dict | None, risk: dict | None, pipeline_run_id: str) -> str:
    cve_id = (vuln or {}).get("cve_id", patch["vulnerability_id"])
    summary = (vuln or {}).get("summary", "")
    severity = (vuln or {}).get("severity", "unknown")
    risk_score = (risk or {}).get("risk_score", "n/a")
    confidence = (risk or {}).get("confidence_score", "n/a")
    evidence = (risk or {}).get("evidence", []) or []
    changes = patch.get("dependency_changes") or []

    change_lines = "\n".join(
        f"- `{c['package']}`: {c['from_version']} → {c['to_version']}" for c in changes
    ) or "_no dependency changes recorded_"

    evidence_lines = "\n".join(
        f"- `{e.get('file')}` :: `{e.get('symbol')}`" for e in evidence[:5]
    ) or "_no reachability evidence available_"

    return f"""## DependencyMedic Autonomous Remediation

**CVE:** {cve_id} ({severity})
**Risk score:** {risk_score} (confidence {confidence})
**Pipeline run:** {pipeline_run_id} ✅

### Vulnerability
{summary or '_no summary available_'}

### Dependency changes
{change_lines}

### Reachability evidence
{evidence_lines}

### Notes
- Patch attempt: `{patch['_id']}` (attempt #{patch.get('attempt_number', 1)})
- Branch: `{patch['branch_name']}`
- Generated by `remediation_engine`, validated by `gitlab_integration` CI.
- Human approval is required before merge.

### Rollback
Revert this MR to restore `{changes[0]['package'] + ' ' + changes[0]['from_version'] if changes else '<package>'}` if regressions appear.
"""
