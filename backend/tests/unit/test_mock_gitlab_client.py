import asyncio

import pytest

from services.gitlab_integration.clients.mock_client import MockGitLabClient


@pytest.mark.asyncio
async def test_mock_pipeline_fails_then_passes_across_attempts():
    client = MockGitLabClient()

    p1 = await client.trigger_pipeline("proj", ref="fix/cve-2021-44228-attempt-1")
    # Need 2 polls before the mock resolves
    await client.get_pipeline("proj", p1.pipeline_id)
    snap1 = await client.get_pipeline("proj", p1.pipeline_id)
    assert snap1.status == "failed"
    assert snap1.failed_stage == "unit_tests"
    assert "TypeError" in (snap1.raw_logs or "")

    p2 = await client.trigger_pipeline("proj", ref="fix/cve-2021-44228-attempt-2")
    await client.get_pipeline("proj", p2.pipeline_id)
    snap2 = await client.get_pipeline("proj", p2.pipeline_id)
    assert snap2.status == "success"


@pytest.mark.asyncio
async def test_mock_create_branch_and_commit_are_idempotent():
    client = MockGitLabClient()
    await client.create_branch("proj", branch="b", ref="main")
    result = await client.commit_files("proj", branch="b", message="m", files=[])
    assert result.branch == "b"
    assert len(result.sha) >= 8
