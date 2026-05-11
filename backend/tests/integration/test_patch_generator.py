"""End-to-end test of patch_generator.generate_patch with an in-memory Mongo and a stub publisher."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from shared.constants import (
    COLLECTION_DEPENDENCY_SNAPSHOTS,
    COLLECTION_PATCH_ATTEMPTS,
    COLLECTION_REPOSITORIES,
    COLLECTION_VULNERABILITIES,
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
async def patched_db(monkeypatch):
    from mongomock_motor import AsyncMongoMockClient

    from shared.utils import mongo as mongo_mod

    client = AsyncMongoMockClient()
    monkeypatch.setattr(mongo_mod, "_client", client)
    db = client[DB_NAME]

    now = datetime.now(timezone.utc)
    await db[COLLECTION_REPOSITORIES].insert_one(
        {
            "_id": "repo-1",
            "repo_name": "payment-service",
            "gitlab_project_id": "12345",
            "default_branch": "main",
            "languages": ["python"],
            "repo_url": "https://gitlab.com/org/payment-service",
            "ci_enabled": True,
            "status": "active",
            "tags": [],
            "seed_manifests": {
                "requirements.txt": "flask==2.0.0\nlodash-py==1.0.0\n",
            },
            "created_at": now,
            "updated_at": now,
            "created_by": "test",
            "version": 1,
        }
    )
    await db[COLLECTION_VULNERABILITIES].insert_one(
        {
            "_id": "vuln-1",
            "cve_id": "CVE-2026-9999",
            "severity": "high",
            "summary": "issue",
            "affected_packages": [
                {
                    "name": "lodash-py",
                    "ecosystem": "pypi",
                    "affected_versions": "<1.2.3",
                    "fixed_versions": ["1.2.3", "2.0.0"],
                }
            ],
            "source": "test",
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "created_by": "test",
            "version": 1,
        }
    )
    await db[COLLECTION_DEPENDENCY_SNAPSHOTS].insert_one(
        {
            "_id": "snap-1",
            "repository_id": "repo-1",
            "commit_sha": "abc",
            "ecosystem": "pypi",
            "dependencies": [
                {
                    "name": "lodash-py",
                    "version": "1.0.0",
                    "direct": True,
                    "manifest_path": "requirements.txt",
                }
            ],
            "generated_at": now,
            "created_at": now,
            "updated_at": now,
            "created_by": "test",
            "version": 1,
        }
    )
    yield db


async def test_patch_generated_emits_event_and_writes_doc(patched_db):
    from services.remediation_engine.services.patch_generator import generate_patch

    publisher = _StubPublisher()
    patch_id = await generate_patch(
        repository_id="repo-1",
        vulnerability_id="vuln-1",
        correlation_id="corr-1",
        publisher=publisher,  # type: ignore[arg-type]
        attempt_number=1,
    )

    doc = await patched_db[COLLECTION_PATCH_ATTEMPTS].find_one({"_id": patch_id})
    assert doc is not None
    assert doc["branch_name"] == "fix/cve-2026-9999-attempt-1"
    assert doc["dependency_changes"][0] == {
        "package": "lodash-py",
        "from_version": "1.0.0",
        "to_version": "1.2.3",
    }
    assert "lodash-py==1.2.3" in doc["manifest_content"]

    assert len(publisher.events) == 1
    evt = publisher.events[0]
    assert evt.event_type == "patch.generated"
    assert evt.correlation_id == "corr-1"
    assert evt.payload["patch_attempt_id"] == patch_id


async def test_patch_generation_fails_without_seed_manifest(patched_db):
    from services.remediation_engine.services.patch_generator import (
        PatchGenerationError,
        generate_patch,
    )

    await patched_db[COLLECTION_REPOSITORIES].update_one(
        {"_id": "repo-1"}, {"$unset": {"seed_manifests": ""}}
    )
    publisher = _StubPublisher()
    with pytest.raises(PatchGenerationError):
        await generate_patch(
            repository_id="repo-1",
            vulnerability_id="vuln-1",
            correlation_id="c",
            publisher=publisher,  # type: ignore[arg-type]
        )
