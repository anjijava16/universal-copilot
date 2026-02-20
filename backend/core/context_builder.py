"""
core/context_builder.py — LLM Context Assembly
================================================
Assembles the complete prompt sent to the LLM on every agent call.

Layers (injected in this order):
  [1] System prompt (base instructions + machine context)
  [2] Tool definitions (JSON schema of available tools)
  [3] Skill content (from RAG retrieval — injected as tool_result)
  [4] YAML config overrides (if any YAML skill is loaded)
  [5] Conversation history (trimmed if over budget)
  [6] User's current message

Token budget is managed across layers — skills are trimmed first
if context would overflow.
"""

import json
from typing import Any, Optional
from datetime import datetime

import structlog

from core.config import settings
from core.token_counter import count_tokens, count_messages_tokens, TokenBudgetManager
from core.skill_rag import skill_rag_engine
from core.redis_client import redis_client

log = structlog.get_logger(__name__)

# ─── Base System Prompt ───────────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """You are Universal Copilot, an expert AI coding assistant.

## Core Behavior
- Think step-by-step before acting
- Use the `think` tool for complex reasoning before making changes
- Read files before editing them — never assume file contents
- Make the smallest change that solves the problem
- After making changes, verify with available linting/testing tools
- Ask for clarification only when truly ambiguous

## Tool Usage
- Prefer `search_files` to understand the codebase before reading individual files
- Use `run_code` in the sandbox for safe code execution and testing
- Use `web_fetch` to read documentation when uncertain about APIs
- Call `get_file_errors` after edits to catch issues immediately
- Tools that modify the environment (run_terminal, delete_file) require user approval

## Code Quality
- Match existing code style, formatting, and patterns
- Write tests for new functionality when a test framework is present
- Handle errors and edge cases explicitly
- Prefer explicit over implicit

## Communication
- Briefly explain what you're doing before tool calls
- Summarize changes made at the end
- Flag any assumptions you made
"""


def _machine_context() -> str:
    """Inject runtime context (date, timezone, etc.)."""
    return f"""
## Runtime Context
- Current date: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
- Platform: Universal Copilot API
"""


class ContextBuilder:
    """
    Assembles the full message array for each LLM call.

    Usage:
        ctx = await context_builder.build(
            user_id="...",
            model="claude-sonnet-4-6",
            user_message="Refactor this file",
            history=[...],
            skill_ids=["skill-abc", "skill-xyz"],
        )
        # ctx["messages"] → pass directly to litellm.acompletion()
    """

    async def build(
        self,
        user_id: str,
        model: str,
        user_message: str,
        history: list[dict],
        skill_ids: list[str],
        system_prompt_override: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Build the complete context for one LLM call.

        Returns:
        {
            "messages":          [...],   # pass to litellm
            "tools":             [...],   # tool schemas
            "model":             str,
            "temperature":       float,
            "max_tokens":        int,
            "skills_injected":   [skill_id, ...],
            "skill_token_count": int,
            "token_breakdown":   {layer: tokens},
        }
        """
        context_limit = settings.get_context_limit(model)
        budget = TokenBudgetManager(
            model=model,
            context_limit=context_limit,
            output_reserve=settings.RESERVED_OUTPUT_TOKENS,
        )

        # ── [1] Build system prompt ───────────────────────────────────────────
        system_content = BASE_SYSTEM_PROMPT + _machine_context()
        if system_prompt_override:
            system_content += f"\n\n## Additional Instructions\n{system_prompt_override}"

        system_tokens = count_tokens(system_content)
        budget.allocate("system_prompt", system_tokens)

        # ── [2] Load and count tool schemas ───────────────────────────────────
        from core.tools.registry import get_enabled_tools
        tools = await get_enabled_tools(user_id)
        tool_schemas = [t["schema"] for t in tools]

        tool_tokens = count_tokens(json.dumps(tool_schemas))
        budget.allocate("tools", tool_tokens)

        # ── [3] User message tokens ───────────────────────────────────────────
        user_msg_tokens = count_tokens(user_message)
        budget.allocate("user_message", user_msg_tokens)

        # ── [4] Load YAML config skills first (no token cost in context) ───────
        yaml_overrides = await self._load_yaml_configs(user_id, skill_ids)

        # Apply YAML overrides to generation params
        if temperature is None:
            temperature = yaml_overrides.get("temperature", 0.2)
        if max_tokens is None:
            max_tokens = yaml_overrides.get("max_tokens", 8192)

        # ── [5] Skill RAG retrieval ────────────────────────────────────────────
        skill_budget   = budget.remaining() - 2000  # reserve 2k for history
        skill_budget   = max(skill_budget, 0)

        md_skill_ids = await self._get_markdown_skill_ids(user_id, skill_ids)

        skill_content, skills_injected, skill_tokens = (
            await skill_rag_engine.retrieve_for_context(
                query=user_message,
                user_id=user_id,
                skill_ids=md_skill_ids,
                max_tokens=skill_budget,
            )
        )
        budget.allocate("skills", skill_tokens)

        # ── [6] Conversation history (trimmed to fit) ──────────────────────────
        history_budget = budget.remaining()
        trimmed_history = budget.trim_history_to_fit(history, history_budget)
        history_tokens  = count_messages_tokens(trimmed_history)
        budget.allocate("history", history_tokens)

        # ── Assemble messages array ────────────────────────────────────────────
        messages = self._assemble_messages(
            system_content=system_content,
            skill_content=skill_content,
            history=trimmed_history,
            user_message=user_message,
        )

        log.info("context_builder.built",
                 model=model,
                 total_tokens=sum(budget.allocations.values()),
                 skills_injected=skills_injected,
                 history_messages=len(trimmed_history),
                 **budget.summary()["by_layer"])

        return {
            "messages":          messages,
            "tools":             tool_schemas,
            "model":             model,
            "temperature":       temperature,
            "max_tokens":        max_tokens,
            "skills_injected":   skills_injected,
            "skill_token_count": skill_tokens,
            "token_breakdown":   budget.summary()["by_layer"],
        }

    def _assemble_messages(
        self,
        system_content: str,
        skill_content: str,
        history: list[dict],
        user_message: str,
    ) -> list[dict]:
        """
        Build the final messages list.

        Structure:
          [system_message]
          [...history messages (trimmed)]
          [user_message with skill injection appended if any]

        Skill content is injected as a tool_result block inside the
        user message — this is the most effective injection position
        because it's recent and the LLM treats it as actionable context.
        """
        messages = []

        # [1] System message
        messages.append({
            "role": "system",
            "content": system_content,
        })

        # [2] History (trimmed)
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg.get("content", ""),
            })

        # [3] Skill injection + user message
        if skill_content:
            # Inject skills as a preceding assistant + tool_result exchange
            # This mimics how GitHub Copilot injects SKILL.md files
            messages.append({
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Let me review the relevant skill instructions for this task.",
                    },
                    {
                        "type": "tool_use",
                        "id": "skill_injection_001",
                        "name": "read_skill",
                        "input": {"query": user_message[:200]},
                    },
                ],
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "skill_injection_001",
                        "content": skill_content,
                    }
                ],
            })

        # [4] Actual user message
        messages.append({
            "role": "user",
            "content": user_message,
        })

        return messages

    async def _get_markdown_skill_ids(
        self, user_id: str, skill_ids: list[str]
    ) -> list[str]:
        """Filter skill_ids to only .md type (YAML handled separately)."""
        md_ids = []
        for sid in skill_ids:
            raw = await redis_client.get(f"skill:{user_id}:{sid}:meta")
            if raw:
                meta = json.loads(raw)
                if meta.get("file_type") == "md":
                    md_ids.append(sid)
        return md_ids

    async def _load_yaml_configs(
        self, user_id: str, skill_ids: list[str]
    ) -> dict[str, Any]:
        """
        Load YAML config skills and merge them into a single config dict.
        Later YAML skills override earlier ones for the same key.
        """
        merged: dict[str, Any] = {}
        for sid in skill_ids:
            raw = await redis_client.get(f"skill:{user_id}:{sid}:meta")
            if not raw:
                continue
            meta = json.loads(raw)
            if meta.get("file_type") not in ("yml", "yaml"):
                continue

            content = await redis_client.get(f"skill:{user_id}:{sid}:content")
            if content:
                import yaml
                try:
                    config = yaml.safe_load(content) or {}
                    merged.update(config)
                except Exception:
                    pass

        return merged
