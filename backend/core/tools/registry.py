"""
core/tools/registry.py — Tool Registry
=======================================
Central registry mapping tool names → (schema, executor function).
Loaded by ContextBuilder (schemas) and AgentLoop (executors).
"""

import json
from typing import Any, Callable, Awaitable
from core.redis_client import redis_client

# Tool definition: schema for LLM + async executor function
ToolEntry = dict[str, Any]   # {schema: dict, executor: Coroutine}


def _make_schema(
    name: str,
    description: str,
    properties: dict,
    required: list[str],
) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


# ─── Import executors ─────────────────────────────────────────────────────────
# Each executor is an async function: async (args: dict) -> str

from core.tools.file_tools import (
    execute_read_file,
    execute_write_file,
    execute_list_directory,
    execute_delete_file,
    execute_search_files,
)
from core.tools.code_tools import (
    execute_run_code,
    execute_run_terminal,
)
from core.tools.web_tools import (
    execute_web_fetch,
    execute_web_search,
)
from core.tools.think_tool import execute_think


# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, ToolEntry] = {

    # ── File system ──────────────────────────────────────────────────────────
    "read_file": {
        "requires_approval": False,
        "executor": execute_read_file,
        "schema": _make_schema(
            name="read_file",
            description=(
                "Read a range of lines from a file. "
                "Always read before editing. Max 250 lines per call."
            ),
            properties={
                "path":      {"type": "string", "description": "Absolute file path"},
                "startLine": {"type": "integer", "description": "First line (1-indexed)"},
                "endLine":   {"type": "integer", "description": "Last line (inclusive)"},
            },
            required=["path", "startLine", "endLine"],
        ),
    },

    "write_file": {
        "requires_approval": False,
        "executor": execute_write_file,
        "schema": _make_schema(
            name="write_file",
            description="Write content to a file, creating parent directories if needed.",
            properties={
                "path":    {"type": "string"},
                "content": {"type": "string"},
            },
            required=["path", "content"],
        ),
    },

    "list_directory": {
        "requires_approval": False,
        "executor": execute_list_directory,
        "schema": _make_schema(
            name="list_directory",
            description="List files and subdirectories at a path.",
            properties={
                "path":      {"type": "string"},
                "recursive": {"type": "boolean", "default": False},
            },
            required=["path"],
        ),
    },

    "delete_file": {
        "requires_approval": True,
        "executor": execute_delete_file,
        "schema": _make_schema(
            name="delete_file",
            description="Delete a file or empty directory. Requires user approval.",
            properties={"path": {"type": "string"}},
            required=["path"],
        ),
    },

    "search_files": {
        "requires_approval": False,
        "executor": execute_search_files,
        "schema": _make_schema(
            name="search_files",
            description=(
                "Search file contents using regex or keywords. "
                "Returns matching file paths and line numbers."
            ),
            properties={
                "query":    {"type": "string"},
                "path":     {"type": "string", "description": "Root dir (default: /)"},
                "file_ext": {"type": "string", "description": "Extension filter e.g. .py"},
                "top_k":    {"type": "integer", "default": 10},
            },
            required=["query"],
        ),
    },

    # ── Code execution ───────────────────────────────────────────────────────
    "run_code": {
        "requires_approval": True,
        "executor": execute_run_code,
        "schema": _make_schema(
            name="run_code",
            description=(
                "Execute code in an isolated Docker sandbox. "
                "Returns stdout, stderr, and exit_code. "
                "No network access. Supports python, javascript, bash."
            ),
            properties={
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "bash"],
                },
                "code":             {"type": "string"},
                "timeout_seconds":  {"type": "integer", "default": 30, "maximum": 120},
            },
            required=["language", "code"],
        ),
    },

    "run_terminal": {
        "requires_approval": True,
        "executor": execute_run_terminal,
        "schema": _make_schema(
            name="run_terminal",
            description=(
                "Run a shell command in the real local environment. "
                "Requires user approval. Use run_code for sandboxed execution."
            ),
            properties={
                "command":           {"type": "string"},
                "working_directory": {"type": "string"},
            },
            required=["command"],
        ),
    },

    # ── Web ──────────────────────────────────────────────────────────────────
    "web_fetch": {
        "requires_approval": False,
        "executor": execute_web_fetch,
        "schema": _make_schema(
            name="web_fetch",
            description="Fetch and return the text content of a URL.",
            properties={
                "url":           {"type": "string", "format": "uri"},
                "extract_links": {"type": "boolean", "default": False},
            },
            required=["url"],
        ),
    },

    "web_search": {
        "requires_approval": False,
        "executor": execute_web_search,
        "schema": _make_schema(
            name="web_search",
            description=(
                "Search the web and return top results with titles, "
                "URLs, and snippets."
            ),
            properties={
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5, "maximum": 10},
            },
            required=["query"],
        ),
    },

    # ── Reasoning ────────────────────────────────────────────────────────────
    "think": {
        "requires_approval": False,
        "executor": execute_think,
        "schema": _make_schema(
            name="think",
            description=(
                "Internal scratchpad for step-by-step reasoning. "
                "Output is NOT shown to the user. "
                "Use before complex decisions or tool calls."
            ),
            properties={
                "thought": {"type": "string"},
            },
            required=["thought"],
        ),
    },
}


async def get_enabled_tools(user_id: str) -> list[ToolEntry]:
    """
    Return tool entries with user-level enable/disable overrides applied.
    """
    raw = await redis_client.get(f"user:{user_id}:tool_state")
    overrides: dict[str, bool] = json.loads(raw) if raw else {}

    result = []
    for name, entry in TOOL_REGISTRY.items():
        is_enabled = overrides.get(name, True)  # default: enabled
        if is_enabled:
            result.append(entry)
    return result


def get_executor(tool_name: str) -> Callable[[dict], Awaitable[str]] | None:
    """Return the executor function for a tool name."""
    entry = TOOL_REGISTRY.get(tool_name)
    return entry["executor"] if entry else None


def requires_approval(tool_name: str) -> bool:
    """Check if a tool requires human approval before execution."""
    entry = TOOL_REGISTRY.get(tool_name)
    return entry.get("requires_approval", False) if entry else False
