"""Serve search, get_doc and who_knows over stdio with the official MCP Python SDK.

gatedmind serve --index .cache/index-seed1-bm25.sqlite --audit logs/audit.jsonl
"""

from __future__ import annotations

from pathlib import Path

import anyio
import mcp_types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from .audit import AuditLog
from .index import Index
from .tools import TOOLS, Tools


def build_server(tools: Tools) -> Server:
    async def list_tools(ctx, params):
        return types.ListToolsResult(tools=[types.Tool(**t) for t in TOOLS])

    async def call_tool(ctx, params):
        text, is_error = await anyio.to_thread.run_sync(
            tools.call, params.name, dict(params.arguments or {})
        )
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text)], isError=is_error
        )

    return Server("gatedmind", on_list_tools=list_tools, on_call_tool=call_tool)


def serve(index_path: Path, audit_path: Path | None = None) -> None:
    tools = Tools(Index(index_path), AuditLog(audit_path) if audit_path else None)
    server = build_server(tools)

    async def run():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    anyio.run(run)
