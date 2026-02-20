"""
routers/tools.py — Tool Registry & Human-in-the-Loop Approval
==============================================================
GET  /tools                            → list all available tools
GET  /tools/{tool_name}                → get single tool definition
POST /tools/toggle                     → enable / disable a tool
POST /tools/approve                    → approve a pending tool call (HITL)
GET  /tools/pending/{session_id}       → get pending approval requests
POST /tools/mcp/register               → register an MCP server
GET  /tools/mcp                        → list registered MCP servers
DELETE /tools/mcp/{server_name}        → unregister MCP server
"""

import json
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from schemas.models import (
    ToolDefinition, ToolListResponse,
    ToolApprovalRequest, ToolApprovalResponse,
    ToolToggleRequest, ToolApprovalDecision
)
from core.auth import get_current_user
from core.redis_client import redis_client
from core.config import settings

router = APIRouter()

# ─── BUILT-IN TOOL REGISTRY ──────────────────────────────────────────────────
# This is the single source of truth for all tools the agent can use.
# Tools are published to the LLM as JSON Schema in every prompt.

BUILT_IN_TOOLS: list[ToolDefinition] = [

    # ── FILE SYSTEM TOOLS ────────────────────────────────────────────────────
    ToolDefinition(
        name="read_file",
        description=(
            "Read the contents of a file at a given path. "
            "Specify startLine and endLine to read a range. "
            "Never read more than 250 lines at once."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path":      {"type": "string", "description": "Absolute file path"},
                "startLine": {"type": "integer", "description": "First line (1-indexed)"},
                "endLine":   {"type": "integer", "description": "Last line (inclusive)"},
            },
            "required": ["path", "startLine", "endLine"],
        },
        requires_approval=False,
        is_enabled=True,
        category="filesystem",
    ),
    ToolDefinition(
        name="write_file",
        description=(
            "Write or overwrite a file at the given path. "
            "Creates parent directories if they don't exist."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string", "description": "Full file content"},
            },
            "required": ["path", "content"],
        },
        requires_approval=False,
        is_enabled=True,
        category="filesystem",
    ),
    ToolDefinition(
        name="list_directory",
        description="List files and directories at the given path.",
        parameters={
            "type": "object",
            "properties": {
                "path":      {"type": "string"},
                "recursive": {"type": "boolean", "default": False},
            },
            "required": ["path"],
        },
        requires_approval=False,
        is_enabled=True,
        category="filesystem",
    ),
    ToolDefinition(
        name="delete_file",
        description="Delete a file or directory. Use with extreme caution.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
        requires_approval=True,   # Always requires human approval
        is_enabled=True,
        category="filesystem",
    ),
    ToolDefinition(
        name="search_files",
        description=(
            "Hybrid keyword + semantic search over the workspace. "
            "Returns file paths and matching line numbers."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query":    {"type": "string"},
                "path":     {"type": "string", "description": "Search root (default: workspace root)"},
                "file_ext": {"type": "string", "description": "Filter by extension e.g. '.py'"},
                "top_k":    {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
        requires_approval=False,
        is_enabled=True,
        category="filesystem",
    ),

    # ── CODE EXECUTION TOOLS ─────────────────────────────────────────────────
    ToolDefinition(
        name="run_code",
        description=(
            "Execute code in an isolated Docker sandbox. "
            "Supports Python, JavaScript (Node.js), and Bash. "
            "Returns stdout, stderr, and exit code. "
            "Sandbox has no network access and limited filesystem."
        ),
        parameters={
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "bash"],
                },
                "code": {"type": "string"},
                "timeout_seconds": {"type": "integer", "default": 30, "maximum": 120},
            },
            "required": ["language", "code"],
        },
        requires_approval=True,
        is_enabled=True,
        category="code",
    ),
    ToolDefinition(
        name="run_terminal",
        description=(
            "Run a shell command in the user's local terminal. "
            "Use run_code with language=bash for sandboxed execution instead. "
            "This runs in the REAL environment — use cautiously."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command":          {"type": "string"},
                "working_directory": {"type": "string"},
            },
            "required": ["command"],
        },
        requires_approval=True,   # Always needs approval
        is_enabled=True,
        category="code",
    ),

    # ── WEB TOOLS ────────────────────────────────────────────────────────────
    ToolDefinition(
        name="web_fetch",
        description=(
            "Fetch the content of a URL. "
            "Returns the cleaned text content of the page. "
            "Use for reading documentation, APIs, or web pages."
        ),
        parameters={
            "type": "object",
            "properties": {
                "url":           {"type": "string", "format": "uri"},
                "extract_links": {"type": "boolean", "default": False},
            },
            "required": ["url"],
        },
        requires_approval=False,
        is_enabled=True,
        category="web",
    ),
    ToolDefinition(
        name="web_search",
        description=(
            "Search the web and return top results with titles, "
            "URLs, and snippets. Use to find current information."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query":   {"type": "string"},
                "top_k":   {"type": "integer", "default": 5, "maximum": 10},
                "region":  {"type": "string", "description": "Country code e.g. 'us', 'gb'"},
            },
            "required": ["query"],
        },
        requires_approval=False,
        is_enabled=True,
        category="web",
    ),

    # ── REASONING TOOL ───────────────────────────────────────────────────────
    ToolDefinition(
        name="think",
        description=(
            "Use this tool to reason step-by-step before acting. "
            "Write your chain-of-thought here. "
            "This does not produce output visible to the user — "
            "it is internal scratchpad only."
        ),
        parameters={
            "type": "object",
            "properties": {
                "thought": {"type": "string"},
            },
            "required": ["thought"],
        },
        requires_approval=False,
        is_enabled=True,
        category="reasoning",
    ),
]

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in BUILT_IN_TOOLS}


# ─── REDIS KEY HELPERS ────────────────────────────────────────────────────────

def _tool_state_key(user_id: str) -> str:
    """Per-user tool enable/disable overrides."""
    return f"user:{user_id}:tool_state"

def _pending_approval_key(session_id: str) -> str:
    return f"approval:{session_id}:pending"

def _mcp_servers_key(user_id: str) -> str:
    return f"user:{user_id}:mcp_servers"


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=ToolListResponse,
    summary="List all available tools",
    description="Returns all built-in tools plus any registered MCP tools. "
                "User-level enable/disable overrides are applied.",
)
async def list_tools(
    category: Optional[str] = Query(default=None, description="Filter: filesystem|code|web|mcp|reasoning"),
    enabled_only: bool = Query(default=False),
    user=Depends(get_current_user),
) -> ToolListResponse:

    # Get user-level overrides from Redis
    raw_state = await redis_client.get(_tool_state_key(user.id))
    user_overrides: dict[str, bool] = json.loads(raw_state) if raw_state else {}

    tools = []
    for tool in BUILT_IN_TOOLS:
        # Apply user override (if any)
        t = tool.model_copy()
        if tool.name in user_overrides:
            t.is_enabled = user_overrides[tool.name]

        if category and t.category != category:
            continue
        if enabled_only and not t.is_enabled:
            continue

        tools.append(t)

    # Append registered MCP tools
    mcp_raw = await redis_client.get(_mcp_servers_key(user.id))
    if mcp_raw:
        mcp_servers = json.loads(mcp_raw)
        for server in mcp_servers.values():
            for mcp_tool in server.get("tools", []):
                td = ToolDefinition(
                    name=f"{server['name']}__{mcp_tool['name']}",
                    description=mcp_tool.get("description", ""),
                    parameters=mcp_tool.get("parameters", {}),
                    requires_approval=server.get("requires_approval", False),
                    is_enabled=server.get("is_enabled", True),
                    category="mcp",
                )
                tools.append(td)

    return ToolListResponse(tools=tools, total=len(tools))


@router.get(
    "/{tool_name}",
    response_model=ToolDefinition,
    summary="Get a single tool definition",
)
async def get_tool(
    tool_name: str,
    user=Depends(get_current_user),
) -> ToolDefinition:
    tool = _TOOL_MAP.get(tool_name)
    if not tool:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found."
        )
    return tool


@router.post(
    "/toggle",
    summary="Enable or disable a tool",
    description="Enables or disables a tool for the current user. "
                "This overrides the default enabled state. "
                "Useful for restricting which tools an agent can use.",
)
async def toggle_tool(
    body: ToolToggleRequest,
    user=Depends(get_current_user),
):
    if body.tool_name not in _TOOL_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{body.tool_name}' not found."
        )

    raw = await redis_client.get(_tool_state_key(user.id))
    state: dict[str, bool] = json.loads(raw) if raw else {}
    state[body.tool_name] = body.enabled
    await redis_client.set(_tool_state_key(user.id), json.dumps(state))

    return {
        "tool_name": body.tool_name,
        "is_enabled": body.enabled,
        "message": f"Tool '{body.tool_name}' {'enabled' if body.enabled else 'disabled'}.",
    }


# ─── HUMAN-IN-THE-LOOP (HITL) APPROVAL ──────────────────────────────────────

@router.get(
    "/pending/{session_id}",
    summary="Get pending tool approval requests",
    description="Returns all tool calls waiting for human approval in a session. "
                "The agent is PAUSED until each pending call is approved or rejected. "
                "Poll this endpoint from the frontend to show approval UI.",
)
async def get_pending_approvals(
    session_id: str,
    user=Depends(get_current_user),
):
    raw = await redis_client.get(_pending_approval_key(session_id))
    pending = json.loads(raw) if raw else []

    return {
        "session_id": session_id,
        "pending_count": len(pending),
        "pending": pending,
    }


@router.post(
    "/approve",
    response_model=ToolApprovalResponse,
    summary="Approve or reject a pending tool call",
    description="""
Human-in-the-loop approval gate.

When the agent wants to run a `requires_approval=true` tool
(e.g. `run_terminal`, `delete_file`), it pauses and writes
a pending approval request to Redis.

The frontend polls `GET /tools/pending/{session_id}`, shows
the user the tool name + arguments, and calls this endpoint
with `approve` or `reject`.

The agent loop (LangGraph interrupt) is resumed via the
`/chat/resume` endpoint after approval is recorded here.
    """,
)
async def approve_tool(
    body: ToolApprovalRequest,
    user=Depends(get_current_user),
) -> ToolApprovalResponse:

    raw = await redis_client.get(_pending_approval_key(body.session_id))
    pending: list[dict] = json.loads(raw) if raw else []

    # Find the specific call
    call = next(
        (p for p in pending if p["tool_call_id"] == body.tool_call_id), None
    )
    if not call:
        raise HTTPException(
            status_code=404,
            detail=f"No pending approval found for tool_call_id '{body.tool_call_id}'."
        )

    # Record the decision
    call["decision"] = body.decision.value
    call["reason"] = body.reason
    await redis_client.set(
        _pending_approval_key(body.session_id),
        json.dumps(pending),
    )

    action = "approved" if body.decision == ToolApprovalDecision.APPROVE else "rejected"
    return ToolApprovalResponse(
        tool_call_id=body.tool_call_id,
        decision=body.decision,
        message=f"Tool call {action}. Resume session to continue agent.",
    )


# ─── MCP SERVER MANAGEMENT ───────────────────────────────────────────────────

@router.post(
    "/mcp/register",
    status_code=201,
    summary="Register an MCP server",
    description="""
Register an external MCP (Model Context Protocol) server.
The server must be running and reachable at the given URL or command.

**Transport types:**
- `stdio` — local process (command + args)
- `http` — remote HTTP server  
- `sse` — Server-Sent Events transport

Once registered, the server's tools are discovered via MCP's
`tools/list` RPC and added to the tool registry automatically.
    """,
)
async def register_mcp_server(
    body: dict[str, Any],
    user=Depends(get_current_user),
):
    """
    Expected body:
    {
      "name": "github",
      "transport": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {"Authorization": "Bearer ..."},
      "requires_approval": false
    }
    OR for stdio:
    {
      "name": "playwright",
      "transport": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {}
    }
    """
    from core.mcp_client import MCPClient

    name = body.get("name")
    if not name:
        raise HTTPException(status_code=422, detail="'name' is required.")

    # Discover tools from the MCP server
    client = MCPClient(config=body)
    try:
        discovered_tools = await client.list_tools()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to MCP server '{name}': {e}"
        )

    # Save to Redis
    raw = await redis_client.get(_mcp_servers_key(user.id))
    servers: dict[str, Any] = json.loads(raw) if raw else {}
    servers[name] = {**body, "tools": discovered_tools}
    await redis_client.set(_mcp_servers_key(user.id), json.dumps(servers))

    return {
        "name": name,
        "tools_discovered": len(discovered_tools),
        "tools": [t["name"] for t in discovered_tools],
        "message": f"MCP server '{name}' registered with {len(discovered_tools)} tools.",
    }


@router.get(
    "/mcp",
    summary="List registered MCP servers",
    description="Returns all MCP servers registered by the current user "
                "and their discovered tools.",
)
async def list_mcp_servers(user=Depends(get_current_user)):
    raw = await redis_client.get(_mcp_servers_key(user.id))
    servers: dict[str, Any] = json.loads(raw) if raw else {}

    return {
        "mcp_servers": [
            {
                "name": name,
                "transport": cfg.get("transport"),
                "tool_count": len(cfg.get("tools", [])),
                "tools": [t["name"] for t in cfg.get("tools", [])],
                "requires_approval": cfg.get("requires_approval", False),
            }
            for name, cfg in servers.items()
        ],
        "total": len(servers),
    }


@router.delete(
    "/mcp/{server_name}",
    status_code=204,
    summary="Unregister an MCP server",
    description="Removes the MCP server and all its tools from the registry.",
)
async def unregister_mcp_server(
    server_name: str,
    user=Depends(get_current_user),
):
    raw = await redis_client.get(_mcp_servers_key(user.id))
    servers: dict[str, Any] = json.loads(raw) if raw else {}

    if server_name not in servers:
        raise HTTPException(
            status_code=404,
            detail=f"MCP server '{server_name}' not registered."
        )

    del servers[server_name]
    await redis_client.set(_mcp_servers_key(user.id), json.dumps(servers))
