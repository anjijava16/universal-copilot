"""
routers/chat.py — Chat & Agent Loop (The Core Router)
======================================================
POST /chat              → non-streaming chat (waits for full response)
POST /chat/stream       → streaming chat via SSE (recommended)
POST /chat/resume       → resume a paused session (after HITL approval)
GET  /chat/{session_id}/status  → get current agent loop status
POST /chat/{session_id}/cancel  → cancel a running agent loop
GET  /chat/{session_id}/tokens  → get token usage breakdown for session

This is where the LangGraph ReAct loop lives.
Every request here:
  1. Builds context (system + skills + history + user message)
  2. Calls LiteLLM with selected model
  3. Executes tool calls locally
  4. Loops until final text response or HITL interrupt
  5. Persists messages to Redis
  6. Streams tokens back via SSE
"""

import json
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from schemas.models import ChatRequest, ChatResponse, StreamChunk, Message, MessageRole
from core.auth import get_current_user
from core.redis_client import redis_client
from core.context_builder import ContextBuilder
from core.agent_loop import run_agent_loop, resume_agent_loop
from core.config import settings

router = APIRouter()
context_builder = ContextBuilder()

# ─── REDIS KEY HELPERS ────────────────────────────────────────────────────────

def _session_meta_key(user_id: str, session_id: str) -> str:
    return f"session:{user_id}:{session_id}:meta"

def _messages_key(user_id: str, session_id: str) -> str:
    return f"session:{user_id}:{session_id}:messages"

def _agent_status_key(session_id: str) -> str:
    return f"agent:{session_id}:status"


async def _get_session_or_404(user_id: str, session_id: str) -> dict:
    data = await redis_client.get(_session_meta_key(user_id, session_id))
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. "
                   f"Create one via POST /sessions first."
        )
    return json.loads(data)


async def _save_message(user_id: str, session_id: str, message: dict):
    """Append a message to the session's message list in Redis."""
    await redis_client.rpush(
        _messages_key(user_id, session_id),
        json.dumps(message),
    )
    # Update message count in meta
    data = await redis_client.get(_session_meta_key(user_id, session_id))
    if data:
        meta = json.loads(data)
        meta["message_count"] = meta.get("message_count", 0) + 1
        await redis_client.set(
            _session_meta_key(user_id, session_id),
            json.dumps(meta),
            ex=settings.SESSION_TTL_SECONDS,
        )


async def _load_history(user_id: str, session_id: str) -> list[dict]:
    """Load conversation history from Redis."""
    raw = await redis_client.lrange(_messages_key(user_id, session_id), 0, -1)
    return [json.loads(m) for m in raw]


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@router.post(
    "/stream",
    summary="Streaming chat (SSE) — recommended",
    description="""
Main chat endpoint. Streams agent output token-by-token via Server-Sent Events.

**Event types returned in stream:**

| type | description |
|---|---|
| `token` | A single LLM output token |
| `tool_start` | Agent is calling a tool (name + input shown) |
| `tool_result` | Tool execution result |
| `approval_required` | Agent paused — tool needs human approval |
| `error` | Error in agent loop |
| `done` | Final event with usage stats |

**Skill injection:**
- Pass `skill_ids` to inject specific skills.
- If not passed, session's attached skills are used.
- Skills are injected as `tool_result` blocks in the context window.

**Model selection:**
- Pass `model` to override the session's default model for this request.
    """,
)
async def stream_chat(
    body: ChatRequest,
    user=Depends(get_current_user),
) -> EventSourceResponse:

    # ── Load session ──────────────────────────────────────────────────────
    session = await _get_session_or_404(user.id, body.session_id)

    # ── Determine model and skills for this request ───────────────────────
    model      = body.model or session.get("model", settings.DEFAULT_MODEL)
    skill_ids  = body.skill_ids or session.get("loaded_skill_ids", [])

    # ── Load conversation history from Redis ─────────────────────────────
    history = await _load_history(user.id, body.session_id)

    # ── Persist user message ─────────────────────────────────────────────
    user_msg = body.messages[-1].model_dump()
    await _save_message(user.id, body.session_id, user_msg)

    # ── Mark agent as running ─────────────────────────────────────────────
    await redis_client.set(
        _agent_status_key(body.session_id),
        json.dumps({"status": "running", "model": model}),
        ex=300,  # 5 min TTL — auto-expire if crash
    )

    async def event_generator() -> AsyncGenerator[dict, None]:
        """
        Drives the LangGraph ReAct loop and yields SSE events.
        Each iteration of the loop is:
          1. LLM call → returns token stream OR tool_call
          2. If tool_call → execute → yield tool_start + tool_result events
          3. If final text → yield tokens + done event
        """
        tool_calls_made  = []
        skills_injected  = []
        total_usage      = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        assistant_content = ""

        try:
            # Build context: system prompt + skill injection + history + user msg
            context = await context_builder.build(
                user_id=user.id,
                model=model,
                user_message=body.messages[-1].content,
                history=history,
                skill_ids=skill_ids,
                system_prompt_override=body.system_prompt or session.get("system_prompt"),
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            )
            skills_injected = context["skills_injected"]

            # ── Yield skills loaded event (informational) ─────────────────
            if skills_injected:
                yield {
                    "event": "skills_loaded",
                    "data": json.dumps({
                        "type": "skills_loaded",
                        "skill_ids": skills_injected,
                        "token_cost": context["skill_token_count"],
                    }),
                }

            # ── Run the agent loop ────────────────────────────────────────
            async for event in run_agent_loop(
                session_id=body.session_id,
                user_id=user.id,
                messages=context["messages"],
                model=model,
                tools=context["tools"],
            ):
                event_type = event.get("type")

                # ── Stream token ──────────────────────────────────────────
                if event_type == "token":
                    assistant_content += event["content"]
                    yield {
                        "event": "message",
                        "data": json.dumps(StreamChunk(
                            type="token",
                            content=event["content"],
                        ).model_dump()),
                    }

                # ── Tool starting ─────────────────────────────────────────
                elif event_type == "tool_start":
                    tool_calls_made.append(event["tool_name"])
                    yield {
                        "event": "message",
                        "data": json.dumps(StreamChunk(
                            type="tool_start",
                            tool_name=event["tool_name"],
                            tool_input=event.get("tool_input"),
                        ).model_dump()),
                    }

                # ── Tool result ───────────────────────────────────────────
                elif event_type == "tool_result":
                    yield {
                        "event": "message",
                        "data": json.dumps(StreamChunk(
                            type="tool_result",
                            tool_name=event["tool_name"],
                            tool_output=event.get("output"),
                        ).model_dump()),
                    }

                # ── Approval required (HITL pause) ────────────────────────
                elif event_type == "approval_required":
                    yield {
                        "event": "message",
                        "data": json.dumps(StreamChunk(
                            type="approval_required",
                            tool_name=event["tool_name"],
                            tool_input=event.get("tool_input"),
                            content=(
                                f"⏸ Waiting for approval to run: {event['tool_name']}. "
                                f"Use POST /tools/approve then POST /chat/resume."
                            ),
                        ).model_dump()),
                    }
                    # Mark agent as paused
                    await redis_client.set(
                        _agent_status_key(body.session_id),
                        json.dumps({"status": "paused", "waiting_for": event["tool_call_id"]}),
                        ex=settings.APPROVAL_TTL_SECONDS,
                    )
                    return  # Stream ends here; resume via /chat/resume

                # ── Usage stats ───────────────────────────────────────────
                elif event_type == "usage":
                    for k in total_usage:
                        total_usage[k] += event.get(k, 0)

                # ── Error ─────────────────────────────────────────────────
                elif event_type == "error":
                    yield {
                        "event": "message",
                        "data": json.dumps(StreamChunk(
                            type="error",
                            error=event.get("error", "Unknown error in agent loop."),
                        ).model_dump()),
                    }
                    return

            # ── Persist assistant message ─────────────────────────────────
            if assistant_content:
                await _save_message(user.id, body.session_id, {
                    "role": "assistant",
                    "content": assistant_content,
                    "tool_calls_made": tool_calls_made,
                })

            # ── Update session token usage ────────────────────────────────
            data = await redis_client.get(_session_meta_key(user.id, body.session_id))
            if data:
                meta = json.loads(data)
                meta["token_usage_total"] = (
                    meta.get("token_usage_total", 0) + total_usage["total_tokens"]
                )
                await redis_client.set(
                    _session_meta_key(user.id, body.session_id),
                    json.dumps(meta),
                    ex=settings.SESSION_TTL_SECONDS,
                )

            # ── Final done event ──────────────────────────────────────────
            yield {
                "event": "message",
                "data": json.dumps(StreamChunk(
                    type="done",
                    usage=total_usage,
                ).model_dump()),
            }

        except asyncio.CancelledError:
            yield {
                "event": "message",
                "data": json.dumps(StreamChunk(
                    type="error",
                    error="Request was cancelled.",
                ).model_dump()),
            }
        finally:
            # Mark agent as idle
            await redis_client.set(
                _agent_status_key(body.session_id),
                json.dumps({"status": "idle"}),
                ex=300,
            )

    return EventSourceResponse(event_generator())


@router.post(
    "",
    response_model=ChatResponse,
    summary="Non-streaming chat",
    description="Waits for the full agent response before returning. "
                "Use /chat/stream instead for better UX. "
                "Useful for programmatic / API usage where SSE is not convenient.",
)
async def chat(
    body: ChatRequest,
    user=Depends(get_current_user),
) -> ChatResponse:

    session = await _get_session_or_404(user.id, body.session_id)
    model     = body.model or session.get("model", settings.DEFAULT_MODEL)
    skill_ids = body.skill_ids or session.get("loaded_skill_ids", [])
    history   = await _load_history(user.id, body.session_id)

    context = await context_builder.build(
        user_id=user.id,
        model=model,
        user_message=body.messages[-1].content,
        history=history,
        skill_ids=skill_ids,
        system_prompt_override=body.system_prompt or session.get("system_prompt"),
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    )

    # Collect all events from the agent loop (no streaming)
    full_content = ""
    tool_calls_made = []
    usage = {}

    async for event in run_agent_loop(
        session_id=body.session_id,
        user_id=user.id,
        messages=context["messages"],
        model=model,
        tools=context["tools"],
    ):
        if event["type"] == "token":
            full_content += event["content"]
        elif event["type"] == "tool_start":
            tool_calls_made.append(event["tool_name"])
        elif event["type"] == "usage":
            usage = event

    # Persist messages
    await _save_message(user.id, body.session_id, body.messages[-1].model_dump())
    await _save_message(user.id, body.session_id, {
        "role": "assistant",
        "content": full_content,
    })

    import uuid
    return ChatResponse(
        session_id=body.session_id,
        message_id=str(uuid.uuid4()),
        content=full_content,
        model=model,
        usage=usage,
        tool_calls_made=tool_calls_made,
        skills_injected=context["skills_injected"],
        tokens_by_layer=context["token_breakdown"],
    )


@router.post(
    "/resume",
    summary="Resume a paused agent (after HITL approval)",
    description="""
After a tool call is approved or rejected via `POST /tools/approve`,
call this endpoint to resume the paused agent loop.

The agent will:
- If **approved**: execute the tool and continue the ReAct loop
- If **rejected**: tell the LLM the tool was rejected (with optional reason)
  and let the LLM decide what to do next

Returns a streaming SSE response — connect to it the same way as `/chat/stream`.
    """,
)
async def resume_chat(
    session_id: str,
    user=Depends(get_current_user),
) -> EventSourceResponse:

    session = await _get_session_or_404(user.id, session_id)

    # Check there's actually something to resume
    raw_status = await redis_client.get(_agent_status_key(session_id))
    if not raw_status:
        raise HTTPException(status_code=400, detail="No active agent session to resume.")

    status = json.loads(raw_status)
    if status.get("status") != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Agent is not paused. Current status: {status.get('status')}."
        )

    async def resume_generator() -> AsyncGenerator[dict, None]:
        async for event in resume_agent_loop(
            session_id=session_id,
            user_id=user.id,
        ):
            yield {
                "event": "message",
                "data": json.dumps(StreamChunk(**event).model_dump()),
            }

    return EventSourceResponse(resume_generator())


@router.get(
    "/{session_id}/status",
    summary="Get agent loop status",
    description="Returns current status of the agent for a session. "
                "Possible values: idle | running | paused | error.",
)
async def get_agent_status(
    session_id: str,
    user=Depends(get_current_user),
):
    await _get_session_or_404(user.id, session_id)

    raw = await redis_client.get(_agent_status_key(session_id))
    if not raw:
        return {"session_id": session_id, "status": "idle"}

    status = json.loads(raw)
    return {"session_id": session_id, **status}


@router.post(
    "/{session_id}/cancel",
    summary="Cancel a running agent loop",
    description="Cancels the currently running agent loop for a session. "
                "The agent stops after the current tool call completes. "
                "Partial output up to the cancellation is saved.",
)
async def cancel_agent(
    session_id: str,
    user=Depends(get_current_user),
):
    await _get_session_or_404(user.id, session_id)

    # Write a cancel signal to Redis — the agent loop checks this
    await redis_client.set(
        f"agent:{session_id}:cancel",
        "1",
        ex=30,
    )
    await redis_client.set(
        _agent_status_key(session_id),
        json.dumps({"status": "cancelling"}),
        ex=60,
    )

    return {
        "session_id": session_id,
        "message": "Cancel signal sent. Agent will stop after current tool call.",
    }


@router.get(
    "/{session_id}/tokens",
    summary="Get token usage breakdown for session",
    description="Returns detailed token usage for the session: "
                "total used, breakdown by layer (system/skills/history/output), "
                "and remaining budget for the session's current model.",
)
async def get_token_usage(
    session_id: str,
    user=Depends(get_current_user),
):
    session = await _get_session_or_404(user.id, session_id)
    model = session.get("model", settings.DEFAULT_MODEL)

    # Model context limits
    MODEL_LIMITS = {
        "claude-opus-4-6":             200_000,
        "claude-sonnet-4-6":           200_000,
        "claude-haiku-4-5-20251001":   200_000,
        "gpt-4o":                      128_000,
        "gpt-4o-mini":                 128_000,
        "o3-mini":                     200_000,
        "gemini/gemini-2.0-flash":   1_000_000,
        "deepseek/deepseek-chat":       64_000,
    }

    context_limit = MODEL_LIMITS.get(model, 128_000)
    total_used    = session.get("token_usage_total", 0)

    return {
        "session_id":      session_id,
        "model":           model,
        "context_limit":   context_limit,
        "total_used":      total_used,
        "remaining":       context_limit - total_used,
        "utilization_pct": round((total_used / context_limit) * 100, 1),
        "message_count":   session.get("message_count", 0),
        "note": (
            "total_used is cumulative across all turns. "
            "Each request uses a fresh context window — "
            "this tracks lifetime usage for cost monitoring."
        ),
    }
