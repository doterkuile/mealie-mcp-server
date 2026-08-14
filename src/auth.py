"""GitHub OAuth provider + username-allowlist middleware for the remote server.

OAuth is enabled only when GITHUB_OAUTH_CLIENT_ID / GITHUB_OAUTH_CLIENT_SECRET are
set. Without them the server runs unauthenticated — local dev only. When enabled,
only the GitHub usernames in MEALIE_ALLOWED_GITHUB_USERS may call tools.

Only used by remote.py; the stdio entrypoint (server.py) is unaffected.
"""

import os

from fastmcp.exceptions import ToolError
from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware


def allowed_users() -> set[str]:
    """GitHub usernames permitted to call tools, from a comma-separated env var."""
    raw = os.getenv("MEALIE_ALLOWED_GITHUB_USERS", "")
    return {u.strip() for u in raw.split(",") if u.strip()}


def build_auth_provider(base_url: str) -> GitHubProvider | None:
    """Return a GitHubProvider when OAuth creds are configured, else None (dev)."""
    client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None
    if not allowed_users():
        raise ValueError(
            "MEALIE_ALLOWED_GITHUB_USERS must be configured when GitHub OAuth is "
            "enabled to prevent unauthorized access to your Mealie instance."
        )
    return GitHubProvider(
        client_id=client_id,
        client_secret=client_secret,
        base_url=base_url,
        # allowed_client_redirect_uris left at default (None) => all DCR clients
        # accepted (claude.ai web + Claude Desktop/Code). Access is gated by the
        # GitHub login + the username allowlist below.
    )


class GitHubAllowlistMiddleware(Middleware):
    """Reject tool calls from any GitHub user not in MEALIE_ALLOWED_GITHUB_USERS."""

    def __init__(self) -> None:
        super().__init__()
        # Resolved once at startup; the env value is fixed for the process lifetime.
        self._allowed = allowed_users()

    async def on_call_tool(self, context, call_next):
        token = get_access_token()
        login = token.claims.get("login") if token else None
        if self._allowed and login not in self._allowed:
            raise ToolError(f"Access denied: GitHub user {login!r} is not authorized.")
        return await call_next(context)
