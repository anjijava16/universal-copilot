"""
Universal Copilot — FastAPI Application Entry Point
====================================================
Multi-model agent platform with skill file injection,
session management, streaming, and tool execution.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from routers import chat, models, skills, sessions, tools, health
from core.config import settings
from core.redis_client import redis_client


# ─── LIFESPAN (startup / shutdown) ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect Redis. Shutdown: flush connections."""
    await redis_client.connect()
    print("✅ Redis connected")
    yield
    await redis_client.disconnect()
    print("🔌 Redis disconnected")


# ─── APP FACTORY ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Universal Copilot API",
    description="Multi-model AI agent with skill file injection (Claude, GPT-4o, Gemini, DeepSeek)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── MIDDLEWARE ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# ─── ROUTERS ─────────────────────────────────────────────────────────────────

app.include_router(health.router,   prefix="/health",   tags=["Health"])
app.include_router(models.router,   prefix="/models",   tags=["Models"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(skills.router,   prefix="/skills",   tags=["Skills"])
app.include_router(tools.router,    prefix="/tools",    tags=["Tools"])
app.include_router(chat.router,     prefix="/chat",     tags=["Chat"])
