"""
routers/health.py — Health & Readiness Checks
==============================================
GET /health        → overall system health
GET /health/ready  → readiness probe (for k8s / Docker)
GET /health/live   → liveness probe
"""

import time
import asyncio
from fastapi import APIRouter
from schemas.models import HealthResponse, ServiceStatus
from core.redis_client import redis_client
from core.config import settings

router = APIRouter()


# ─── HELPERS ─────────────────────────────────────────────────────────────────

async def _check_redis() -> ServiceStatus:
    try:
        start = time.monotonic()
        await redis_client.ping()
        latency = int((time.monotonic() - start) * 1000)
        return ServiceStatus(name="redis", status="ok", latency_ms=latency)
    except Exception as e:
        return ServiceStatus(name="redis", status="down", detail=str(e))


async def _check_litellm() -> ServiceStatus:
    """Ping LiteLLM proxy or a cheap model call to verify connectivity."""
    try:
        import litellm
        start = time.monotonic()
        # cheapest possible call — 1 token
        await litellm.acompletion(
            model="claude-haiku-4-5-20251001",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
        )
        latency = int((time.monotonic() - start) * 1000)
        return ServiceStatus(name="litellm", status="ok", latency_ms=latency)
    except Exception as e:
        return ServiceStatus(name="litellm", status="degraded", detail=str(e))


async def _check_vector_store() -> ServiceStatus:
    try:
        from core.skill_rag import skill_rag_engine
        start = time.monotonic()
        skill_rag_engine.ping()
        latency = int((time.monotonic() - start) * 1000)
        return ServiceStatus(name="vector_store", status="ok", latency_ms=latency)
    except Exception as e:
        return ServiceStatus(name="vector_store", status="degraded", detail=str(e))


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=HealthResponse,
    summary="Full system health check",
    description="Checks Redis, LiteLLM proxy, and vector store. "
                "Returns overall status and per-service detail.",
)
async def health_check() -> HealthResponse:
    services = await asyncio.gather(
        _check_redis(),
        _check_litellm(),
        _check_vector_store(),
    )
    services = list(services)

    # overall = worst individual status
    if any(s.status == "down" for s in services):
        overall = "down"
    elif any(s.status == "degraded" for s in services):
        overall = "degraded"
    else:
        overall = "ok"

    return HealthResponse(
        status=overall,
        version=settings.APP_VERSION,
        services=services,
    )


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 if app is ready to receive traffic "
                "(Redis connected). Used by Kubernetes readiness probe.",
)
async def readiness_probe():
    """Kubernetes readiness probe — only checks Redis."""
    status = await _check_redis()
    if status.status != "ok":
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Redis not available")
    return {"status": "ready"}


@router.get(
    "/live",
    summary="Liveness probe",
    description="Returns 200 if process is alive. No external checks.",
)
async def liveness_probe():
    """Kubernetes liveness probe — just confirms process is running."""
    return {"status": "alive", "version": settings.APP_VERSION}
