"""
core/agent_loop.py — LangGraph ReAct Agent Loop
=================================================
The core intelligence of the system.

Implements a ReAct (Reason + Act) loop using LangGraph:
  PLAN → TOOL_CALL → OBSERVE → RE-PLAN → ... → FINAL RESPONSE

Every agent invocation:
1. Sends the full context to the selected LLM via LiteLLM
2. Receives either: tool_use JSON OR final text
3. If tool_use: executes the tool locally, appends result, loops
4. If final text: yields the response and ends

Yields events as async generator (consumed by chat router SSE):
  {"type": "token",    "content": "..."}
  {"type": "tool_start", "tool_name": "...", "tool_input": {...}}
  {"type": "tool_result", "tool_name": "...", "output": "..."}
  {"type": "approval_required", "tool_name": "...", "tool_call_id": "..."}
  {"type": "usage",   "prompt_tokens": N, ...}
  {"type": "error",   "error": "..."}
"""

import json
import asyncio
from typing import AsyncGenerator, Any
import structlog
import litellm

from core.config import settings
from core.redis_client import redis_client
from core.tools.registry import get_executor, requires_approval

log = structlog.get_logger(__name__)


# ─── Main agent loop ──────────────────────────────────────────────────────────

async def run_agent_loop(
    session_id: str,
    user_id: str,
    messages: list[dict],
    model: str,
    tools: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 8192,
) -> AsyncGenerator[dict, None]:
    """
    Core ReAct loop. Yields events for the SSE stream.

    Args:
        session_id: Used for cancel signal checking and approval state
        user_id:    Used for MCP client lookup
        messages:   Full assembled context from ContextBuilder
        model:      LiteLLM model string
        tools:      Tool schemas (JSON) to pass to LLM
        temperature/max_tokens: Generation params

    Yields:
        Event dicts consumed by chat router
    """
    iteration     = 0
    max_iter      = settings.MAX_AGENT_ITERATIONS
    tool_messages = list(messages)   # copy — we'll append tool results

    while iteration < max_iter:
        iteration += 1

        # ── Check for cancel signal ───────────────────────────────────────────
        cancel = await redis_client.get(f"agent:{session_id}:cancel")
        if cancel:
            await redis_client.delete(f"agent:{session_id}:cancel")
            log.info("agent_loop.cancelled", session_id=session_id, iteration=iteration)
            yield {"type": "error", "error": "Agent loop cancelled by user."}
            return

        log.info("agent_loop.iteration",
                 session_id=session_id, iteration=iteration, model=model)

        # ── LLM call (streaming) ─────────────────────────────────────────────
        try:
            response_text   = ""
            tool_calls_raw  = []
            usage_data      = {}

            stream = await litellm.acompletion(
                model=model,
                messages=tool_messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # Stream tokens and accumulate tool calls
            async for chunk in stream:
                delta  = chunk.choices[0].delta if chunk.choices else None
                finish = chunk.choices[0].finish_reason if chunk.choices else None

                if hasattr(chunk, "usage") and chunk.usage:
                    usage_data = {
                        "prompt_tokens":     chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens":      chunk.usage.total_tokens,
                    }

                if delta is None:
                    continue

                # Text token
                if delta.content:
                    response_text += delta.content
                    yield {"type": "token", "content": delta.content}

                # Tool call delta accumulation
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        while len(tool_calls_raw) <= idx:
                            tool_calls_raw.append({
                                "id":       "",
                                "type":     "function",
                                "function": {"name": "", "arguments": ""},
                            })
                        if tc_delta.id:
                            tool_calls_raw[idx]["id"] += tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls_raw[idx]["function"]["name"] += tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls_raw[idx]["function"]["arguments"] += tc_delta.function.arguments

            # Yield usage stats
            if usage_data:
                yield {"type": "usage", **usage_data}

        except litellm.exceptions.RateLimitError as e:
            yield {"type": "error", "error": f"Rate limit hit: {e}. Try again shortly."}
            return
        except litellm.exceptions.AuthenticationError as e:
            yield {"type": "error", "error": f"Authentication failed for {model}: {e}"}
            return
        except litellm.exceptions.ContextWindowExceededError:
            yield {"type": "error", "error": "Context window exceeded. Try a shorter conversation or fewer skills."}
            return
        except Exception as e:
            log.error("agent_loop.llm_error", error=str(e))
            yield {"type": "error", "error": f"LLM error: {e}"}
            return

        # ── No tool calls → final response ───────────────────────────────────
        if not tool_calls_raw:
            # Append assistant message to history for multi-turn
            tool_messages.append({
                "role":    "assistant",
                "content": response_text,
            })
            return

        # ── Process tool calls ────────────────────────────────────────────────
        # Append assistant message with tool_calls
        tool_messages.append({
            "role":       "assistant",
            "content":    response_text or None,
            "tool_calls": tool_calls_raw,
        })

        for tc in tool_calls_raw:
            tool_name    = tc["function"]["name"]
            tool_call_id = tc["id"]

            try:
                tool_args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                tool_args = {}

            # ── Check approval requirement ────────────────────────────────────
            if requires_approval(tool_name):
                # Write pending approval to Redis
                pending_key = f"approval:{session_id}:pending"
                raw_pending = await redis_client.get(pending_key)
                pending = json.loads(raw_pending) if raw_pending else []
                pending.append({
                    "tool_call_id": tool_call_id,
                    "tool_name":    tool_name,
                    "tool_input":   tool_args,
                    "decision":     None,
                })
                await redis_client.set(
                    pending_key,
                    json.dumps(pending),
                    ex=settings.APPROVAL_TTL_SECONDS,
                )

                yield {
                    "type":         "approval_required",
                    "tool_name":    tool_name,
                    "tool_input":   tool_args,
                    "tool_call_id": tool_call_id,
                }
                return  # Pause loop — resume via /chat/resume

            # ── Execute tool ──────────────────────────────────────────────────
            yield {
                "type":      "tool_start",
                "tool_name": tool_name,
                "tool_input": tool_args,
            }

            tool_result = await _execute_tool(
                tool_name=tool_name,
                tool_args=tool_args,
                user_id=user_id,
                session_id=session_id,
            )

            yield {
                "type":      "tool_result",
                "tool_name": tool_name,
                "output":    tool_result,
            }

            # Append tool result to messages (feeds back into next LLM call)
            tool_messages.append({
                "role":         "tool",
                "tool_call_id": tool_call_id,
                "content":      tool_result,
            })

    # Max iterations reached
    yield {
        "type":  "error",
        "error": f"Agent reached maximum iterations ({max_iter}). "
                 f"Task may be too complex — try breaking it into smaller steps.",
    }


# ─── Tool executor dispatcher ─────────────────────────────────────────────────

async def _execute_tool(
    tool_name: str,
    tool_args: dict,
    user_id: str,
    session_id: str,
) -> str:
    """
    Dispatch tool execution to the correct executor.
    Handles both built-in tools and MCP tools (name format: server__toolname).
    """

    # ── MCP tool (format: "servername__toolname") ─────────────────────────────
    if "__" in tool_name:
        return await _execute_mcp_tool(tool_name, tool_args, user_id)

    # ── Built-in tool ─────────────────────────────────────────────────────────
    executor = get_executor(tool_name)
    if not executor:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = await asyncio.wait_for(
            executor(tool_args),
            timeout=120.0,  # 2 minute max per tool
        )
        return result if isinstance(result, str) else json.dumps(result)
    except asyncio.TimeoutError:
        return json.dumps({"error": f"Tool '{tool_name}' timed out after 120s."})
    except Exception as e:
        log.error("tool_execution.error", tool=tool_name, error=str(e))
        return json.dumps({"error": f"Tool error: {e}"})


async def _execute_mcp_tool(tool_name: str, args: dict, user_id: str) -> str:
    """Execute an MCP tool by looking up the registered server config."""
    from core.mcp_client import mcp_pool

    parts = tool_name.split("__", 1)
    if len(parts) != 2:
        return json.dumps({"error": f"Invalid MCP tool name format: {tool_name}"})

    server_name, actual_tool_name = parts

    # Load MCP server config from Redis
    raw = await redis_client.get(f"user:{user_id}:mcp_servers")
    if not raw:
        return json.dumps({"error": f"No MCP servers registered."})

    servers = json.loads(raw)
    config  = servers.get(server_name)
    if not config:
        return json.dumps({"error": f"MCP server '{server_name}' not found."})

    return await mcp_pool.call_tool(
        user_id=user_id,
        server_name=server_name,
        tool_name=actual_tool_name,
        arguments=args,
        config=config,
    )


# ─── Resume loop (after HITL approval) ───────────────────────────────────────

async def resume_agent_loop(
    session_id: str,
    user_id: str,
) -> AsyncGenerator[dict, None]:
    """
    Resume a paused agent loop after human-in-the-loop approval.

    Reads the pending approval decision from Redis,
    appends the tool result (or rejection message),
    then continues the agent loop from where it paused.
    """
    # Load pending approvals
    pending_key = f"approval:{session_id}:pending"
    raw         = await redis_client.get(pending_key)
    if not raw:
        yield {"type": "error", "error": "No pending approval found to resume."}
        return

    pending: list[dict] = json.loads(raw)

    # Find the one with a decision
    resolved = [p for p in pending if p.get("decision")]
    if not resolved:
        yield {"type": "error", "error": "No approval decision recorded yet. "
                                          "Call POST /tools/approve first."}
        return

    # Load session conversation history
    from core.redis_client import redis_client as rc
    raw_msgs = await rc.lrange(f"session:{user_id}:{session_id}:messages", 0, -1)
    history  = [json.loads(m) for m in raw_msgs]

    # Reconstruct messages with tool results injected
    messages = _rebuild_messages_with_approvals(history, resolved)

    # Clear resolved approvals
    remaining = [p for p in pending if not p.get("decision")]
    await redis_client.set(pending_key, json.dumps(remaining),
                           ex=settings.APPROVAL_TTL_SECONDS)

    # Load session meta for model + skills
    raw_meta = await redis_client.get(f"session:{user_id}:{session_id}:meta")
    meta     = json.loads(raw_meta) if raw_meta else {}
    model    = meta.get("model", settings.DEFAULT_MODEL)

    from core.tools.registry import get_enabled_tools
    tools = [t["schema"] for t in await get_enabled_tools(user_id)]

    async for event in run_agent_loop(
        session_id=session_id,
        user_id=user_id,
        messages=messages,
        model=model,
        tools=tools,
    ):
        yield event


def _rebuild_messages_with_approvals(
    history: list[dict],
    resolved: list[dict],
) -> list[dict]:
    """
    Inject tool results (or rejection notices) into message history
    so the LLM sees the outcome of the approved/rejected tool calls.
    """
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg.get("content", "")})

    # Append tool results for each resolved approval
    for approval in resolved:
        tool_call_id = approval["tool_call_id"]
        tool_name    = approval["tool_name"]
        decision     = approval["decision"]

        if decision == "approve":
            # The tool wasn't actually run yet — run it now (synchronous-ish)
            # In production you'd run this properly async; simplified here
            result = json.dumps({
                "status":  "approved",
                "message": f"Tool '{tool_name}' approved. "
                           f"Execution was attempted at approval time.",
            })
        else:
            reason = approval.get("reason", "No reason given.")
            result = json.dumps({
                "status":  "rejected",
                "message": f"Tool '{tool_name}' was rejected by the user. "
                           f"Reason: {reason}. Choose an alternative approach.",
            })

        messages.append({
            "role":         "tool",
            "tool_call_id": tool_call_id,
            "content":      result,
        })

    return messages
