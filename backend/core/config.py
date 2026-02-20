"""
core/config.py — Centralized Application Settings
===================================================
Uses pydantic-settings to load from environment variables / .env file.
All other modules import `settings` from here — never read env vars directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # ── Auth ─────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-must-be-at-least-32-chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"
    SESSION_TTL_SECONDS: int = 604800   # 7 days
    SKILL_TTL_SECONDS: int = 2592000    # 30 days
    APPROVAL_TTL_SECONDS: int = 3600    # 1 hour

    # ── LLM API Keys ──────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    # ── LLM Defaults ─────────────────────────────────────────────────────────
    DEFAULT_MODEL: str = "claude-sonnet-4-6"
    MAX_AGENT_ITERATIONS: int = 20
    RESERVED_OUTPUT_TOKENS: int = 8192  # always reserve for LLM response

    # ── File Limits ───────────────────────────────────────────────────────────
    MAX_SKILL_FILE_SIZE_BYTES: int = 524288  # 512 KB

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    FAISS_INDEX_PATH: str = "./data/faiss_index"

    # ── Docker Sandbox ────────────────────────────────────────────────────────
    DOCKER_SANDBOX_IMAGE: str = "python:3.12-slim"
    SANDBOX_TIMEOUT_SECONDS: int = 30
    SANDBOX_MEMORY_LIMIT: str = "256m"
    SANDBOX_CPU_QUOTA: int = 50000

    # ── Web Search (optional) ─────────────────────────────────────────────────
    BRAVE_SEARCH_API_KEY: str = ""

    # ── Context Window limits per model ──────────────────────────────────────
    @property
    def MODEL_CONTEXT_LIMITS(self) -> dict[str, int]:
        return {
            "claude-opus-4-6":                  200_000,
            "claude-sonnet-4-6":                200_000,
            "claude-haiku-4-5-20251001":        200_000,
            "gpt-4o":                           128_000,
            "gpt-4o-mini":                      128_000,
            "o3-mini":                          200_000,
            "gemini/gemini-2.0-flash":        1_000_000,
            "gemini/gemini-2.0-flash-thinking-exp": 1_000_000,
            "deepseek/deepseek-chat":            64_000,
            "deepseek/deepseek-reasoner":        64_000,
        }

    def get_context_limit(self, model: str) -> int:
        return self.MODEL_CONTEXT_LIMITS.get(model, 128_000)


# Singleton — import this everywhere
settings = Settings()
