"""Pick a GitLab client based on configuration."""

from __future__ import annotations

from .gitlab_client import GitLabHttpClient
from .mock_client import MockGitLabClient
from .protocol import GitLabClient


def make_client(*, gitlab_url: str, gitlab_token: str) -> GitLabClient:
    if not gitlab_token:
        return MockGitLabClient()
    return GitLabHttpClient(base_url=gitlab_url, token=gitlab_token)
