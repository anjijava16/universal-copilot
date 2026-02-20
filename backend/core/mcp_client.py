"""
core/mcp_client.py — MCP (Model Context Protocol) Client
==========================================================
Implements the MCP client side of the JSON-RPC protocol.

Supports two transports:
  - stdio  → spawns a local process, communicates over stdin/stdout
  - http   → sends POST requests to a remote MCP server

MCP spec: https://modelcontextprotocol.io/docs/
"""

import json
import asyncio
import httpx
from typing import Any
import structlog

log = structlog.get_logger(__name__)


class MCPClient:
    """
    MCP Client for communicating with MCP servers.

    Usage:
        client = MCPClient(config={
            "transport": "http",
            "url": "https://api.githubcopilot.com/mcp/",
            "headers": {"Authorization": "Bearer ..."}
        })
        tools = await client.list_tools()
        result = await client.call_tool("create_issue", {"title": "Bug", "body": "..."})
    """

    def __init__(self, config: dict[str, Any]):
        self.config    = config
        self.transport = config.get("transport", "http")
        self._process: asyncio.subprocess.Process | None = None
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    # ── HTTP transport ────────────────────────────────────────────────────────

    async def _http_request(self, method: str, params: dict = None) -> Any:
        url     = self.config.get("url", "")
        headers = {
            "Content-Type": "application/json",
            **self.config.get("headers", {}),
        }
        payload = {
            "jsonrpc": "2.0",
            "id":      self._next_id(),
            "method":  method,
            "params":  params or {},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise RuntimeError(
                f"MCP server error: {data['error'].get('message', data['error'])}"
            )
        return data.get("result")

    # ── Stdio transport ───────────────────────────────────────────────────────

    async def _ensure_process(self):
        """Start the stdio MCP server process if not already running."""
        if self._process and self._process.returncode is None:
            return

        cmd  = self.config.get("command", "")
        args = self.config.get("args", [])
        env  = {**__import__("os").environ, **self.config.get("env", {})}

        self._process = await asyncio.create_subprocess_exec(
            cmd, *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        log.info("mcp.process_started", command=cmd, pid=self._process.pid)

        # Initialize session
        await self._stdio_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities":    {},
            "clientInfo":      {"name": "universal-copilot", "version": "1.0.0"},
        })

    async def _stdio_request(self, method: str, params: dict = None) -> Any:
        await self._ensure_process()
        proc = self._process

        payload = json.dumps({
            "jsonrpc": "2.0",
            "id":      self._next_id(),
            "method":  method,
            "params":  params or {},
        }) + "\n"

        proc.stdin.write(payload.encode())
        await proc.stdin.drain()

        # Read response line
        try:
            line = await asyncio.wait_for(
                proc.stdout.readline(), timeout=30.0
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"MCP stdio timeout waiting for response to {method}")

        data = json.loads(line.decode())
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        return data.get("result")

    async def _request(self, method: str, params: dict = None) -> Any:
        if self.transport == "http":
            return await self._http_request(method, params)
        elif self.transport in ("stdio", "sse"):
            return await self._stdio_request(method, params)
        else:
            raise ValueError(f"Unknown MCP transport: {self.transport}")

    # ── Public API ────────────────────────────────────────────────────────────

    async def list_tools(self) -> list[dict]:
        """
        Discover available tools from the MCP server.
        Returns list of {name, description, parameters} dicts.
        """
        result = await self._request("tools/list")
        tools  = result.get("tools", []) if result else []
        log.info("mcp.tools_listed", count=len(tools))
        return [
            {
                "name":        t.get("name"),
                "description": t.get("description", ""),
                "parameters":  t.get("inputSchema", {}),
            }
            for t in tools
        ]

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Call an MCP tool and return its result as a string.
        This is the executor called by the agent loop for MCP tools.
        """
        log.info("mcp.tool_call", tool=tool_name)
        try:
            result = await self._request("tools/call", {
                "name":      tool_name,
                "arguments": arguments,
            })
            # MCP tool results can be text, JSON, or resource references
            if isinstance(result, dict):
                content = result.get("content", [])
                if isinstance(content, list):
                    texts = [
                        c.get("text", "") for c in content
                        if c.get("type") == "text"
                    ]
                    return "\n".join(texts) or json.dumps(result)
                return json.dumps(content)
            return json.dumps(result)
        except Exception as e:
            log.error("mcp.tool_error", tool=tool_name, error=str(e))
            return json.dumps({"error": str(e)})

    async def close(self):
        """Clean up stdio process if running."""
        if self._process and self._process.returncode is None:
            self._process.terminate()
            await self._process.wait()
            log.info("mcp.process_terminated")


class MCPClientPool:
    """
    Manages a pool of MCP clients per user.
    Clients are created lazily and reused across requests.
    """

    def __init__(self):
        # user_id → {server_name → MCPClient}
        self._clients: dict[str, dict[str, MCPClient]] = {}

    def get_or_create(
        self, user_id: str, server_name: str, config: dict
    ) -> MCPClient:
        if user_id not in self._clients:
            self._clients[user_id] = {}
        if server_name not in self._clients[user_id]:
            self._clients[user_id][server_name] = MCPClient(config)
        return self._clients[user_id][server_name]

    async def call_tool(
        self,
        user_id: str,
        server_name: str,
        tool_name: str,
        arguments: dict,
        config: dict,
    ) -> str:
        client = self.get_or_create(user_id, server_name, config)
        return await client.call_tool(tool_name, arguments)

    async def close_all(self, user_id: str):
        for client in self._clients.get(user_id, {}).values():
            await client.close()
        self._clients.pop(user_id, None)


mcp_pool = MCPClientPool()
