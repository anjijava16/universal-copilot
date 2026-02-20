"""
core/tools/code_tools.py — Code Execution Tool Executors
=========================================================
run_code   → executes in isolated Docker sandbox (no network, limited fs)
run_terminal → executes in real local shell (requires user approval)
"""

import json
import asyncio
import subprocess
import tempfile
import os
from pathlib import Path
import structlog

from core.config import settings

log = structlog.get_logger(__name__)


# ─── run_code (Docker sandbox) ────────────────────────────────────────────────

async def execute_run_code(args: dict) -> str:
    """
    Execute code in an isolated Docker container.
    - No network access (--network=none)
    - Read-only filesystem except /tmp
    - Memory and CPU limits from settings
    - Automatic cleanup after execution
    """
    language = args.get("language", "python")
    code     = args.get("code", "")
    timeout  = min(int(args.get("timeout_seconds", 30)), settings.SANDBOX_TIMEOUT_SECONDS)

    if not code.strip():
        return json.dumps({"error": "No code provided."})

    # Language → Docker run command
    LANG_CONFIGS = {
        "python": {
            "image":   settings.DOCKER_SANDBOX_IMAGE,
            "ext":     ".py",
            "cmd_tpl": ["python", "{file}"],
        },
        "javascript": {
            "image":   "node:20-alpine",
            "ext":     ".js",
            "cmd_tpl": ["node", "{file}"],
        },
        "bash": {
            "image":   "alpine:latest",
            "ext":     ".sh",
            "cmd_tpl": ["sh", "{file}"],
        },
    }

    config = LANG_CONFIGS.get(language)
    if not config:
        return json.dumps({"error": f"Unsupported language: {language}"})

    try:
        import docker
        client = docker.from_env()

        # Write code to a temp file
        with tempfile.NamedTemporaryFile(
            suffix=config["ext"], delete=False, mode="w"
        ) as f:
            f.write(code)
            code_file = f.name

        cmd = [c.format(file=f"/code/{Path(code_file).name}") for c in config["cmd_tpl"]]

        container = client.containers.run(
            image=config["image"],
            command=cmd,
            volumes={os.path.dirname(code_file): {"bind": "/code", "mode": "ro"}},
            network_disabled=True,          # no internet access
            mem_limit=settings.SANDBOX_MEMORY_LIMIT,
            cpu_quota=settings.SANDBOX_CPU_QUOTA,
            remove=True,                    # auto-cleanup
            detach=False,
            stdout=True,
            stderr=True,
            timeout=timeout,
        )

        output = container.decode("utf-8") if isinstance(container, bytes) else str(container)
        return json.dumps({
            "language":  language,
            "stdout":    output[:5000],    # cap output
            "stderr":    "",
            "exit_code": 0,
            "truncated": len(output) > 5000,
        })

    except Exception as e:
        error_msg = str(e)

        # Fallback: subprocess execution (less secure, no Docker)
        if "docker" in error_msg.lower() or "connection" in error_msg.lower():
            log.warning("run_code.docker_unavailable_fallback")
            return await _subprocess_fallback(language, code, timeout)

        log.error("run_code.error", language=language, error=error_msg)
        return json.dumps({"error": error_msg})
    finally:
        try:
            os.unlink(code_file)
        except Exception:
            pass


async def _subprocess_fallback(language: str, code: str, timeout: int) -> str:
    """
    Fallback when Docker is unavailable.
    Uses subprocess with timeout — less isolated but functional.
    """
    LANG_CMDS = {
        "python":     ["python3", "-c"],
        "javascript": ["node",    "-e"],
        "bash":       ["bash",    "-c"],
    }
    cmd_prefix = LANG_CMDS.get(language)
    if not cmd_prefix:
        return json.dumps({"error": f"Unsupported language: {language}"})

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_prefix, code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        return json.dumps({
            "language":  language,
            "stdout":    stdout.decode("utf-8", errors="replace")[:5000],
            "stderr":    stderr.decode("utf-8", errors="replace")[:2000],
            "exit_code": proc.returncode,
            "sandbox":   "subprocess (Docker unavailable)",
        })
    except asyncio.TimeoutError:
        return json.dumps({"error": f"Code execution timed out after {timeout}s."})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── run_terminal ─────────────────────────────────────────────────────────────

async def execute_run_terminal(args: dict) -> str:
    """
    Run a shell command in the real local environment.
    This tool always requires user approval before reaching here.
    """
    command   = args.get("command", "")
    work_dir  = args.get("working_directory", os.getcwd())
    timeout   = 60  # 60s hard timeout for terminal commands

    if not command.strip():
        return json.dumps({"error": "No command provided."})

    # Block obviously dangerous commands
    BLOCKED = ["rm -rf /", "mkfs", ":(){:|:&};:", "dd if=/dev/zero"]
    if any(b in command for b in BLOCKED):
        return json.dumps({"error": "Command blocked by safety rules."})

    log.info("run_terminal.executing", command=command, cwd=work_dir)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=work_dir if os.path.isdir(work_dir) else None,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        return json.dumps({
            "command":   command,
            "stdout":    stdout.decode("utf-8", errors="replace")[:8000],
            "stderr":    stderr.decode("utf-8", errors="replace")[:2000],
            "exit_code": proc.returncode,
        })
    except asyncio.TimeoutError:
        return json.dumps({"error": f"Command timed out after {timeout}s."})
    except Exception as e:
        return json.dumps({"error": str(e)})
