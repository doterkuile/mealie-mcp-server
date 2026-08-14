#!/usr/bin/env python3
"""Remote (HTTP) entrypoint — serves this MCP server to claude.ai over a tunnel.

server.py builds a stdio FastMCP 1.x server with all the Mealie tools and prompts
registered. FastMCP 2's `as_proxy` wraps that object in-process, which is what
lets us add OAuth + HTTP transport without touching any of the tool modules (so
the fork stays trivially rebaseable on upstream).

    uv run mealie-mcp-remote     # serves the MCP endpoint at http://host:port/mcp/
"""

import logging
import os

from fastmcp import FastMCP

from auth import GitHubAllowlistMiddleware, build_auth_provider
from server import mcp as stdio_mcp

logger = logging.getLogger("mealie-mcp")


def main() -> None:
    host = os.getenv("MEALIE_MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MEALIE_MCP_PORT", "8003"))
    # Public URL behind the Cloudflare tunnel; falls back to host:port for local dev.
    base_url = os.getenv("MEALIE_MCP_BASE_URL") or f"http://{host}:{port}"

    auth = build_auth_provider(base_url)
    mcp = FastMCP.as_proxy(stdio_mcp, name="mealie", auth=auth)
    if auth:
        mcp.add_middleware(GitHubAllowlistMiddleware())

    logger.info(
        {
            "message": "Starting Mealie MCP Server (http)",
            "url": f"http://{host}:{port}/mcp/",
            "auth": "on" if auth else "off (local dev)",
        }
    )
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()
