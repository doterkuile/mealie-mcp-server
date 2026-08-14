"""The auth gate for the remote (HTTP) entrypoint.

The dangerous branch is a public endpoint that ends up with OAuth on but no
allowlist, so anyone with a GitHub account could call the tools.
"""

import pytest

from auth import build_auth_provider

BASE_URL = "https://mcp-recipes.example"


def test_no_creds_means_no_auth(monkeypatch):
    monkeypatch.delenv("GITHUB_OAUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("GITHUB_OAUTH_CLIENT_SECRET", raising=False)
    assert build_auth_provider(BASE_URL) is None


def test_oauth_without_allowlist_refuses_to_start(monkeypatch):
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "id")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "secret")
    monkeypatch.setenv("MEALIE_ALLOWED_GITHUB_USERS", "  , ")
    with pytest.raises(ValueError, match="MEALIE_ALLOWED_GITHUB_USERS"):
        build_auth_provider(BASE_URL)


def test_oauth_with_allowlist(monkeypatch):
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "id")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "secret")
    monkeypatch.setenv("MEALIE_ALLOWED_GITHUB_USERS", "doterkuile")
    assert build_auth_provider(BASE_URL) is not None
