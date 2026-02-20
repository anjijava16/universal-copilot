"""
core/tools/file_tools.py — File System Tool Executors
======================================================
Each function is an async executor called by the agent loop
when the LLM requests that tool.

Input:  dict of tool arguments (from LLM tool_call)
Output: str (shown to LLM as tool_result content)
"""

import os
import re
import json
from pathlib import Path
from typing import Any
import structlog

log = structlog.get_logger(__name__)

# Safety: restrict file operations to these root paths
ALLOWED_ROOTS = ["/workspace", "/tmp", "/home", os.getcwd()]


def _is_safe_path(path_str: str) -> bool:
    """Prevent path traversal outside allowed roots."""
    try:
        resolved = Path(path_str).resolve()
        return any(
            str(resolved).startswith(str(Path(root).resolve()))
            for root in ALLOWED_ROOTS
        )
    except Exception:
        return False


# ─── read_file ────────────────────────────────────────────────────────────────

async def execute_read_file(args: dict) -> str:
    path      = args.get("path", "")
    start     = max(1, int(args.get("startLine", 1)))
    end       = int(args.get("endLine", start + 249))
    max_lines = 250

    if not _is_safe_path(path):
        return json.dumps({"error": f"Path '{path}' is not in an allowed directory."})

    try:
        file_path = Path(path)
        if not file_path.exists():
            return json.dumps({"error": f"File not found: {path}"})
        if not file_path.is_file():
            return json.dumps({"error": f"Path is not a file: {path}"})

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()

        total_lines = len(all_lines)
        end = min(end, start + max_lines - 1, total_lines)

        selected = all_lines[start - 1: end]
        content  = "".join(selected)

        return json.dumps({
            "path":        path,
            "startLine":   start,
            "endLine":     end,
            "totalLines":  total_lines,
            "content":     content,
            "hasMore":     end < total_lines,
        })
    except UnicodeDecodeError:
        return json.dumps({"error": f"File is binary or has encoding issues: {path}"})
    except Exception as e:
        log.error("read_file.error", path=path, error=str(e))
        return json.dumps({"error": str(e)})


# ─── write_file ───────────────────────────────────────────────────────────────

async def execute_write_file(args: dict) -> str:
    path    = args.get("path", "")
    content = args.get("content", "")

    if not _is_safe_path(path):
        return json.dumps({"error": f"Path '{path}' is not allowed."})

    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        lines      = content.count("\n") + 1
        size_bytes = len(content.encode("utf-8"))

        log.info("write_file.success", path=path, lines=lines, bytes=size_bytes)
        return json.dumps({
            "success":   True,
            "path":      path,
            "lines":     lines,
            "sizeBytes": size_bytes,
        })
    except Exception as e:
        log.error("write_file.error", path=path, error=str(e))
        return json.dumps({"error": str(e)})


# ─── list_directory ───────────────────────────────────────────────────────────

async def execute_list_directory(args: dict) -> str:
    path      = args.get("path", ".")
    recursive = bool(args.get("recursive", False))

    if not _is_safe_path(path):
        return json.dumps({"error": f"Path '{path}' is not allowed."})

    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return json.dumps({"error": f"Directory not found: {path}"})
        if not dir_path.is_dir():
            return json.dumps({"error": f"Path is not a directory: {path}"})

        entries = []

        if recursive:
            for item in sorted(dir_path.rglob("*")):
                # Skip hidden files and common noise dirs
                if any(p.startswith(".") for p in item.parts):
                    continue
                if any(n in item.parts for n in ("node_modules", "__pycache__", ".git")):
                    continue
                entries.append({
                    "path": str(item.relative_to(dir_path)),
                    "type": "file" if item.is_file() else "directory",
                    "size": item.stat().st_size if item.is_file() else None,
                })
                if len(entries) >= 200:
                    entries.append({"truncated": True})
                    break
        else:
            for item in sorted(dir_path.iterdir()):
                entries.append({
                    "name": item.name,
                    "type": "file" if item.is_file() else "directory",
                    "size": item.stat().st_size if item.is_file() else None,
                })

        return json.dumps({"path": path, "entries": entries, "count": len(entries)})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── delete_file ──────────────────────────────────────────────────────────────

async def execute_delete_file(args: dict) -> str:
    path = args.get("path", "")

    if not _is_safe_path(path):
        return json.dumps({"error": f"Path '{path}' is not allowed."})

    try:
        file_path = Path(path)
        if not file_path.exists():
            return json.dumps({"error": f"Path not found: {path}"})

        if file_path.is_file():
            file_path.unlink()
            action = "file_deleted"
        elif file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
            action = "directory_deleted"
        else:
            return json.dumps({"error": "Unknown path type."})

        log.warning("delete_file.executed", path=path, action=action)
        return json.dumps({"success": True, "path": path, "action": action})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── search_files ─────────────────────────────────────────────────────────────

async def execute_search_files(args: dict) -> str:
    query    = args.get("query", "")
    root     = args.get("path", ".")
    file_ext = args.get("file_ext", "")
    top_k    = min(int(args.get("top_k", 10)), 50)

    if not _is_safe_path(root):
        return json.dumps({"error": f"Path '{root}' is not allowed."})

    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    results = []
    root_path = Path(root)

    for file_path in sorted(root_path.rglob("*")):
        if len(results) >= top_k:
            break

        # Skip noise
        if any(p.startswith(".") for p in file_path.parts):
            continue
        if any(n in file_path.parts for n in ("node_modules", "__pycache__", ".git")):
            continue
        if not file_path.is_file():
            continue
        if file_ext and not file_path.suffix == file_ext:
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            matches = []
            for lineno, line in enumerate(lines, 1):
                if pattern.search(line):
                    matches.append({
                        "line":    lineno,
                        "content": line.rstrip(),
                    })
                    if len(matches) >= 5:
                        break

            if matches:
                results.append({
                    "file":    str(file_path),
                    "matches": matches,
                })
        except Exception:
            continue

    return json.dumps({
        "query":   query,
        "root":    root,
        "results": results,
        "count":   len(results),
    })
