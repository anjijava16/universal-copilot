"""
routers/skills.py — Skill File Management
==========================================
POST   /skills/upload            → upload .md or .yml skill file
GET    /skills                   → list all skills (with metadata)
GET    /skills/{skill_id}        → get single skill metadata
GET    /skills/{skill_id}/content → get raw file content
POST   /skills/search            → semantic search over skill chunks
DELETE /skills/{skill_id}        → delete skill + embeddings
POST   /skills/{skill_id}/embed  → (re)embed skill into vector store
GET    /skills/{skill_id}/preview → preview how skill injects into context

.md files  → parsed as instruction skills (task prompts, rules, examples)
.yml files → parsed as config (model params, tool defs, constraints)
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter, HTTPException, Depends,
    UploadFile, File, Form, Query, BackgroundTasks
)

from schemas.models import (
    SkillMetadata, SkillUploadResponse,
    SkillListResponse, SkillSearchResponse,
    SkillSearchResult, SkillFileType
)
from core.auth import get_current_user
from core.redis_client import redis_client
from core.skill_parser import SkillParser
from core.skill_rag import skill_rag_engine
from core.token_counter import count_tokens
from core.config import settings

router = APIRouter()
parser = SkillParser()

# ─── REDIS KEY HELPERS ────────────────────────────────────────────────────────

def _skill_key(user_id: str, skill_id: str) -> str:
    return f"skill:{user_id}:{skill_id}:meta"

def _skill_content_key(user_id: str, skill_id: str) -> str:
    return f"skill:{user_id}:{skill_id}:content"

def _user_skills_key(user_id: str) -> str:
    return f"user:{user_id}:skills"


async def _get_skill_or_404(user_id: str, skill_id: str) -> dict:
    data = await redis_client.get(_skill_key(user_id, skill_id))
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found."
        )
    return json.loads(data)


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=SkillUploadResponse,
    status_code=201,
    summary="Upload a skill file (.md or .yml)",
    description="""
Upload a `.md` or `.yml` skill file.

**Markdown (.md)** — instruction skill:
- Parsed into sections by `##` headings
- Frontmatter (YAML `---` block) extracted for metadata
- Embedded into vector store for RAG retrieval

**YAML (.yml / .yaml)** — config skill:
- Defines model params, tool overrides, system constraints
- Loaded as structured config, not embedded into vector store

Files are stored in Redis + FAISS. No disk storage.
    """,
)
async def upload_skill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(default=None, description="Display name (defaults to filename)"),
    description: Optional[str] = Form(default=None),
    triggers: Optional[str] = Form(
        default=None,
        description="Comma-separated keywords that auto-activate this skill"
    ),
    user=Depends(get_current_user),
) -> SkillUploadResponse:

    # ── Validate file type ────────────────────────────────────────────────
    filename = file.filename or "unnamed"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ("md", "yml", "yaml"):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '.{ext}'. "
                   f"Only .md, .yml, and .yaml are accepted."
        )

    # ── Read content ─────────────────────────────────────────────────────
    raw_bytes = await file.read()
    if len(raw_bytes) > settings.MAX_SKILL_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: "
                   f"{settings.MAX_SKILL_FILE_SIZE_BYTES // 1024}KB."
        )

    content = raw_bytes.decode("utf-8")

    # ── Parse ─────────────────────────────────────────────────────────────
    if ext == "md":
        parsed = parser.parse_markdown(content)
        file_type = SkillFileType.MARKDOWN
    else:
        parsed = parser.parse_yaml(content)
        file_type = SkillFileType.YAML

    # ── Build metadata ────────────────────────────────────────────────────
    skill_id = str(uuid.uuid4())
    skill_name = name or parsed.get("name") or filename.rsplit(".", 1)[0]
    trigger_list = [t.strip() for t in (triggers or "").split(",") if t.strip()]
    token_count = count_tokens(content)
    now = datetime.now(timezone.utc).isoformat()

    meta = {
        "skill_id": skill_id,
        "user_id": user.id,
        "name": skill_name,
        "description": description or parsed.get("description"),
        "file_type": file_type.value,
        "file_name": filename,
        "token_count": token_count,
        "section_count": len(parsed.get("sections", [])),
        "triggers": trigger_list or parsed.get("triggers", []),
        "is_embedded": False,
        "created_at": now,
        "updated_at": now,
    }

    # ── Persist to Redis ──────────────────────────────────────────────────
    await redis_client.set(
        _skill_key(user.id, skill_id),
        json.dumps(meta),
        ex=settings.SKILL_TTL_SECONDS,
    )
    await redis_client.set(
        _skill_content_key(user.id, skill_id),
        content,
        ex=settings.SKILL_TTL_SECONDS,
    )
    await redis_client.sadd(_user_skills_key(user.id), skill_id)

    # ── Embed in background (non-blocking) ───────────────────────────────
    if file_type == SkillFileType.MARKDOWN:
        background_tasks.add_task(
            _embed_skill_background,
            user_id=user.id,
            skill_id=skill_id,
            content=content,
            sections=parsed.get("sections", []),
        )

    return SkillUploadResponse(
        skill_id=skill_id,
        name=skill_name,
        file_name=filename,
        file_type=file_type,
        token_count=token_count,
        section_count=meta["section_count"],
        message=(
            f"Skill uploaded. "
            + ("Embedding in background..." if file_type == SkillFileType.MARKDOWN
               else "YAML config parsed and ready.")
        ),
    )


async def _embed_skill_background(
    user_id: str, skill_id: str, content: str, sections: list[dict]
):
    """Background task: embed skill chunks into FAISS vector store."""
    try:
        await skill_rag_engine.embed_skill(
            skill_id=skill_id,
            user_id=user_id,
            sections=sections,
            full_content=content,
        )
        # Mark as embedded
        data = await redis_client.get(_skill_key(user_id, skill_id))
        if data:
            meta = json.loads(data)
            meta["is_embedded"] = True
            meta["updated_at"] = datetime.now(timezone.utc).isoformat()
            await redis_client.set(
                _skill_key(user_id, skill_id),
                json.dumps(meta),
                ex=settings.SKILL_TTL_SECONDS,
            )
    except Exception as e:
        print(f"[SKILL EMBED ERROR] skill_id={skill_id}: {e}")


@router.get(
    "",
    response_model=SkillListResponse,
    summary="List all skills",
    description="Returns all uploaded skills for the current user. "
                "Filter by file type with ?file_type=md or ?file_type=yml.",
)
async def list_skills(
    file_type: Optional[SkillFileType] = Query(default=None),
    embedded_only: bool = Query(default=False),
    user=Depends(get_current_user),
) -> SkillListResponse:

    skill_ids = await redis_client.smembers(_user_skills_key(user.id))
    skills = []

    for sid in skill_ids:
        data = await redis_client.get(_skill_key(user.id, sid))
        if not data:
            continue
        m = json.loads(data)

        if file_type and m["file_type"] != file_type.value:
            continue
        if embedded_only and not m.get("is_embedded"):
            continue

        skills.append(SkillMetadata(**m))

    skills.sort(key=lambda s: s.created_at, reverse=True)
    total_tokens = sum(s.token_count for s in skills)

    return SkillListResponse(
        skills=skills,
        total=len(skills),
        total_tokens=total_tokens,
    )


@router.get(
    "/{skill_id}",
    response_model=SkillMetadata,
    summary="Get skill metadata",
)
async def get_skill(
    skill_id: str,
    user=Depends(get_current_user),
) -> SkillMetadata:
    meta = await _get_skill_or_404(user.id, skill_id)
    return SkillMetadata(**meta)


@router.get(
    "/{skill_id}/content",
    summary="Get raw skill file content",
    description="Returns the raw text content of the skill file. "
                "Useful for previewing or editing skill files in the UI.",
)
async def get_skill_content(
    skill_id: str,
    user=Depends(get_current_user),
):
    await _get_skill_or_404(user.id, skill_id)
    content = await redis_client.get(_skill_content_key(user.id, skill_id))
    if not content:
        raise HTTPException(status_code=404, detail="Skill content not found.")

    return {"skill_id": skill_id, "content": content}


@router.get(
    "/{skill_id}/preview",
    summary="Preview how skill injects into context",
    description="Shows exactly what will be injected into the LLM context "
                "window when this skill is active. "
                "Includes token count and message structure.",
)
async def preview_skill_injection(
    skill_id: str,
    user=Depends(get_current_user),
):
    meta = await _get_skill_or_404(user.id, skill_id)
    content = await redis_client.get(_skill_content_key(user.id, skill_id))
    if not content:
        raise HTTPException(status_code=404, detail="Skill content not found.")

    # Simulates what Context Builder does
    injected_message = {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "skill_load_preview",
                "content": content,
            }
        ],
    }

    return {
        "skill_id": skill_id,
        "skill_name": meta["name"],
        "token_count": meta["token_count"],
        "injection_position": "After system prompt, before conversation history",
        "injected_as": "tool_result block inside a user message",
        "preview_message": injected_message,
        "note": (
            "This content is appended to the message array on every LLM call "
            "where this skill is active. It does NOT persist between sessions — "
            "it is re-injected on each request."
        ),
    }


@router.post(
    "/search",
    response_model=SkillSearchResponse,
    summary="Semantic search over skill content",
    description="Searches all embedded skills using vector similarity. "
                "Returns the most relevant sections ranked by similarity score. "
                "This is the same retrieval used by the RAG engine at query time.",
)
async def search_skills(
    query: str = Query(..., min_length=1, description="Natural language search query"),
    top_k: int = Query(default=5, ge=1, le=20),
    min_score: float = Query(default=0.5, ge=0.0, le=1.0),
    user=Depends(get_current_user),
) -> SkillSearchResponse:

    raw_results = await skill_rag_engine.search(
        query=query,
        user_id=user.id,
        top_k=top_k,
        min_score=min_score,
    )

    results = [
        SkillSearchResult(
            skill_id=r["skill_id"],
            skill_name=r["skill_name"],
            section_title=r["section_title"],
            content=r["content"],
            similarity_score=r["score"],
            token_count=count_tokens(r["content"]),
        )
        for r in raw_results
    ]

    return SkillSearchResponse(
        query=query,
        results=results,
        total_tokens=sum(r.token_count for r in results),
    )


@router.post(
    "/{skill_id}/embed",
    summary="(Re)embed a skill into the vector store",
    description="Manually triggers embedding for a skill. "
                "Useful if embedding failed in the background after upload, "
                "or if you want to force a refresh after editing.",
)
async def embed_skill(
    skill_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    meta = await _get_skill_or_404(user.id, skill_id)

    if meta["file_type"] != SkillFileType.MARKDOWN.value:
        raise HTTPException(
            status_code=400,
            detail="Only .md skills can be embedded. "
                   "YAML config files are not embedded into the vector store."
        )

    content = await redis_client.get(_skill_content_key(user.id, skill_id))
    if not content:
        raise HTTPException(status_code=404, detail="Skill content not found.")

    parsed = parser.parse_markdown(content)
    background_tasks.add_task(
        _embed_skill_background,
        user_id=user.id,
        skill_id=skill_id,
        content=content,
        sections=parsed.get("sections", []),
    )

    return {
        "skill_id": skill_id,
        "message": "Embedding started in background. "
                   "Check GET /skills/{skill_id} for is_embedded status."
    }


@router.delete(
    "/{skill_id}",
    status_code=204,
    summary="Delete a skill",
    description="Permanently deletes the skill, its content, and its embeddings. "
                "Sessions that reference this skill will no longer inject it.",
)
async def delete_skill(
    skill_id: str,
    user=Depends(get_current_user),
):
    await _get_skill_or_404(user.id, skill_id)

    # Delete from FAISS vector store
    await skill_rag_engine.delete_skill(skill_id=skill_id, user_id=user.id)

    # Delete from Redis
    await redis_client.delete(_skill_key(user.id, skill_id))
    await redis_client.delete(_skill_content_key(user.id, skill_id))
    await redis_client.srem(_user_skills_key(user.id), skill_id)
