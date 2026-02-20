"""
routers/sessions.py — Conversation Session Management
======================================================
POST   /sessions                        → create new session
GET    /sessions                        → list user's sessions
GET    /sessions/{session_id}           → get session detail + history
DELETE /sessions/{session_id}           → delete session
DELETE /sessions/{session_id}/messages → clear history, keep session
GET    /sessions/{session_id}/messages  → get message history (paginated)
POST   /sessions/{session_id}/skills    → attach skills to session
DELETE /sessions/{session_id}/skills/{skill_id} → detach skill
GET    /sessions/{session_id}/export    → export session as JSON/markdown

All state stored in Redis with TTL (default: 7 days).
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from schemas.models import (
    SessionCreateRequest, SessionResponse, SessionListResponse, Message
)
from core.redis_client import redis_client
from core.auth import get_current_user
from core.config import settings

router = APIRouter()

# ─── REDIS KEY HELPERS ────────────────────────────────────────────────────────

def _session_key(user_id: str, session_id: str) -> str:
    return f"session:{user_id}:{session_id}:meta"

def _messages_key(user_id: str, session_id: str) -> str:
    return f"session:{user_id}:{session_id}:messages"

def _user_sessions_key(user_id: str) -> str:
    return f"user:{user_id}:sessions"


# ─── INTERNAL HELPERS ─────────────────────────────────────────────────────────

async def _get_session_or_404(user_id: str, session_id: str) -> dict:
    data = await redis_client.get(_session_key(user_id, session_id))
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found."
        )
    return json.loads(data)


async def _save_session(user_id: str, session_id: str, meta: dict):
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    await redis_client.set(
        _session_key(user_id, session_id),
        json.dumps(meta),
        ex=settings.SESSION_TTL_SECONDS,   # default: 7 days
    )
    # Track this session in user's index
    await redis_client.sadd(_user_sessions_key(user_id), session_id)


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=SessionResponse,
    status_code=201,
    summary="Create a new session",
    description="Creates a new conversation session. "
                "Optionally attach skill IDs and a system prompt override. "
                "Returns session_id to use in all subsequent chat requests.",
)
async def create_session(
    body: SessionCreateRequest,
    user=Depends(get_current_user),
) -> SessionResponse:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    meta = {
        "session_id": session_id,
        "user_id": user.id,
        "model": body.model,
        "system_prompt": body.system_prompt,
        "loaded_skill_ids": body.skill_ids,
        "token_usage_total": 0,
        "message_count": 0,
        "metadata": body.metadata,
        "created_at": now,
        "updated_at": now,
    }

    await _save_session(user.id, session_id, meta)

    return SessionResponse(
        session_id=session_id,
        model=meta["model"],
        created_at=meta["created_at"],
        updated_at=meta["updated_at"],
        message_count=0,
        loaded_skill_ids=body.skill_ids,
        token_usage_total=0,
        metadata=body.metadata,
    )


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List all sessions for current user",
    description="Paginated list of sessions sorted by last updated descending.",
)
async def list_sessions(
    limit:  int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0,  ge=0),
    user=Depends(get_current_user),
) -> SessionListResponse:
    session_ids = await redis_client.smembers(_user_sessions_key(user.id))
    sessions = []

    for sid in session_ids:
        data = await redis_client.get(_session_key(user.id, sid))
        if data:
            m = json.loads(data)
            sessions.append(SessionResponse(
                session_id=m["session_id"],
                model=m["model"],
                created_at=m["created_at"],
                updated_at=m["updated_at"],
                message_count=m["message_count"],
                loaded_skill_ids=m["loaded_skill_ids"],
                token_usage_total=m["token_usage_total"],
                metadata=m.get("metadata", {}),
            ))

    # Sort by updated_at descending
    sessions.sort(key=lambda s: s.updated_at, reverse=True)
    total = len(sessions)
    sessions = sessions[offset: offset + limit]

    return SessionListResponse(sessions=sessions, total=total)


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session metadata",
    description="Returns session metadata. "
                "For full message history use GET /sessions/{id}/messages.",
)
async def get_session(
    session_id: str,
    user=Depends(get_current_user),
) -> SessionResponse:
    meta = await _get_session_or_404(user.id, session_id)
    return SessionResponse(
        session_id=meta["session_id"],
        model=meta["model"],
        created_at=meta["created_at"],
        updated_at=meta["updated_at"],
        message_count=meta["message_count"],
        loaded_skill_ids=meta["loaded_skill_ids"],
        token_usage_total=meta["token_usage_total"],
        metadata=meta.get("metadata", {}),
    )


@router.delete(
    "/{session_id}",
    status_code=204,
    summary="Delete a session",
    description="Permanently deletes session metadata and all messages.",
)
async def delete_session(
    session_id: str,
    user=Depends(get_current_user),
):
    await _get_session_or_404(user.id, session_id)  # 404 if not found
    await redis_client.delete(_session_key(user.id, session_id))
    await redis_client.delete(_messages_key(user.id, session_id))
    await redis_client.srem(_user_sessions_key(user.id), session_id)


@router.get(
    "/{session_id}/messages",
    summary="Get paginated message history",
    description="Returns messages for a session. "
                "Paginate with limit/offset. "
                "Messages are stored in insertion order.",
)
async def get_messages(
    session_id: str,
    limit:  int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
):
    await _get_session_or_404(user.id, session_id)

    raw = await redis_client.lrange(
        _messages_key(user.id, session_id), offset, offset + limit - 1
    )
    messages = [json.loads(m) for m in raw]
    total = await redis_client.llen(_messages_key(user.id, session_id))

    return {
        "session_id": session_id,
        "messages": messages,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete(
    "/{session_id}/messages",
    status_code=204,
    summary="Clear message history",
    description="Wipes all messages from the session but keeps the session "
                "metadata (model, skills, etc.) intact. "
                "Effectively starts a fresh conversation.",
)
async def clear_messages(
    session_id: str,
    user=Depends(get_current_user),
):
    meta = await _get_session_or_404(user.id, session_id)
    await redis_client.delete(_messages_key(user.id, session_id))

    # Reset counters
    meta["message_count"] = 0
    meta["token_usage_total"] = 0
    await _save_session(user.id, session_id, meta)


@router.post(
    "/{session_id}/skills",
    summary="Attach skills to session",
    description="Attaches one or more skill IDs to an existing session. "
                "These skills will be injected into every subsequent "
                "chat request for this session.",
)
async def attach_skills(
    session_id: str,
    skill_ids: list[str],
    user=Depends(get_current_user),
):
    meta = await _get_session_or_404(user.id, session_id)

    # Merge without duplicates, preserving order
    existing = set(meta.get("loaded_skill_ids", []))
    new_ids = [s for s in skill_ids if s not in existing]
    meta["loaded_skill_ids"] = meta.get("loaded_skill_ids", []) + new_ids

    await _save_session(user.id, session_id, meta)

    return {
        "session_id": session_id,
        "loaded_skill_ids": meta["loaded_skill_ids"],
        "added": new_ids,
        "message": f"Added {len(new_ids)} skill(s). "
                   f"Total: {len(meta['loaded_skill_ids'])}."
    }


@router.delete(
    "/{session_id}/skills/{skill_id}",
    summary="Detach a skill from session",
    description="Removes a skill from the session's active skill list. "
                "Does NOT delete the skill from the system.",
)
async def detach_skill(
    session_id: str,
    skill_id: str,
    user=Depends(get_current_user),
):
    meta = await _get_session_or_404(user.id, session_id)

    before = meta.get("loaded_skill_ids", [])
    meta["loaded_skill_ids"] = [s for s in before if s != skill_id]

    if len(meta["loaded_skill_ids"]) == len(before):
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' is not attached to this session."
        )

    await _save_session(user.id, session_id, meta)
    return {
        "session_id": session_id,
        "removed_skill_id": skill_id,
        "loaded_skill_ids": meta["loaded_skill_ids"],
    }


@router.get(
    "/{session_id}/export",
    summary="Export session as JSON or Markdown",
    description="Downloads the full session (metadata + messages) "
                "as either JSON or Markdown. "
                "Use ?format=markdown for human-readable export.",
)
async def export_session(
    session_id: str,
    format: Literal["json", "markdown"] = Query(default="json"),
    user=Depends(get_current_user),
):
    meta = await _get_session_or_404(user.id, session_id)

    raw_messages = await redis_client.lrange(
        _messages_key(user.id, session_id), 0, -1
    )
    messages = [json.loads(m) for m in raw_messages]

    if format == "json":
        payload = json.dumps(
            {"session": meta, "messages": messages},
            indent=2
        )
        return StreamingResponse(
            iter([payload]),
            media_type="application/json",
            headers={
                "Content-Disposition":
                    f'attachment; filename="session-{session_id}.json"'
            },
        )

    # Markdown export
    lines = [
        f"# Conversation Export",
        f"",
        f"**Session ID:** `{session_id}`",
        f"**Model:** `{meta['model']}`",
        f"**Created:** {meta['created_at']}",
        f"**Messages:** {len(messages)}",
        f"",
        f"---",
        f"",
    ]
    for msg in messages:
        role_label = msg["role"].upper()
        lines.append(f"### {role_label}")
        lines.append(f"")
        lines.append(msg.get("content", "_(no content)_"))
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    md_content = "\n".join(lines)
    return StreamingResponse(
        iter([md_content]),
        media_type="text/markdown",
        headers={
            "Content-Disposition":
                f'attachment; filename="session-{session_id}.md"'
        },
    )
