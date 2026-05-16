"""Integration test: full patch.generated -> ci.started/failed/validated flow with the mock GitLab client."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from shared.constants import (
    COLLECTION_PATCH_ATTEMPTS,
    COLLECTION_PIPELINE_RUNS,
    COLLECTION_REPOSITORIES,
    DB_NAME,
)
from shared.events.base import BaseEvent


class _StubPublisher:
    def __init__(self) -> None:
        self.events: list[BaseEvent] = []

    async def publish(self, event: BaseEvent) -> str:
        self.events.append(event)
        return "stub-id"


@pytest.fixture
async def db(monkeypatch):
    from mongomock_motor import AsyncMongoMockClient

    from shared.utils import mongo as mongo_mod

    client = AsyncMongoMockClient()
    monkeypatch.setattr(mongo_mod, "_client", client)
    return client[DB_NAME]


async def _seed_patch(db, attempt_number: int, branch_name: str) -> str:
    now = datetime.now(timezone.utc)
    await db[COLLECTION_REPOSITORIES].insert_one(
        {
            "_id": "repo-1",
            "repo_name": "payment-service",
            "gitlab_project_id": "12345",
            "default_branch": "main",
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "created_by": "test",
            "version": 1,
        }
    )
    await db[COLLECTION_PATCH_ATTEMPTS].insert_one(
        {
            "_id": "patch-1",
            "repository_id": "repo-1",
            "vulnerability_id": "vuln-1",
            "branch_name": branch_name,
            "manifest_path": "requirements.txt",
            "manifest_content": "lodash-py==1.2.3\n",
            "dependency_changes": [
                {"package": "lodash-py", "from_version": "1.0.0", "to_version": "1.2.3"}
            ],
            "attempt_number": attempt_number,
            "status": "generated",
            "patch_summary": "bump",
            "created_at": now,
            "updated_at": now,
            "created_by": "test",
            "version": 1,
        }
    )
    return "patch-1"


async def test_failing_pipeline_emits_ci_failed(db):
    from services.gitlab_integration.clients.mock_client import MockGitLabClient
    from services.gitlab_integration.services.pipeline_runner import run_patch_pipeline

    await _seed_patch(db, attempt_number=1, branch_name="fix/cve-2026-1-attempt-1")
    publisher = _StubPublisher()
    client = MockGitLabClient()

    await run_patch_pipeline(
        client=client,
        publisher=publisher,  # type: ignore[arg-type]
        patch_attempt_id="patch-1",
        correlation_id="c1",
        poll_interval=0.0,
        poll_timeout=2.0,
    )

    types = [e.event_type for e in publisher.events]
    assert "ci.started" in types
    assert "pipeline.completed" in types
    assert "ci.failed" in types
    assert "patch.validated" not in types

    pipeline_doc = await db[COLLECTION_PIPELINE_RUNS].find_one({})
    assert pipeline_doc["status"] == "failed"
    assert pipeline_doc["failed_stage"] == "unit_tests"


async def test_passing_pipeline_emits_patch_validated(db):
    from services.gitlab_integration.clients.mock_client import MockGitLabClient
    from services.gitlab_integration.services.pipeline_runner import run_patch_pipeline

    await _seed_patch(db, attempt_number=2, branch_name="fix/cve-2026-1-attempt-2")
    publisher = _StubPublisher()
    client = MockGitLabClient()

    await run_patch_pipeline(
        client=client,
        publisher=publisher,  # type: ignore[arg-type]
        patch_attempt_id="patch-1",
        correlation_id="c2",
        poll_interval=0.0,
        poll_timeout=2.0,
    )

    types = [e.event_type for e in publisher.events]
    assert "ci.started" in types
    assert "pipeline.completed" in types
    assert "patch.validated" in types
    assert "ci.failed" not in types
