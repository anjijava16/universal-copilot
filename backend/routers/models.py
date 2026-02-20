"""
routers/models.py — Model Discovery & Validation
=================================================
GET  /models              → list all supported models
GET  /models/{model_id}   → get single model info
POST /models/validate     → test a model (ping with 1-token call)
GET  /models/providers    → list providers (Anthropic, OpenAI, etc.)
"""

import time
from fastapi import APIRouter, HTTPException, Depends
from schemas.models import (
    ModelInfo, ModelListResponse, ModelProvider,
    ModelValidateRequest, ModelValidateResponse
)
from core.auth import get_current_user
from core.config import settings

router = APIRouter()

# ─── SUPPORTED MODEL CATALOG ─────────────────────────────────────────────────
# LiteLLM model strings → metadata
# Add new models here; router picks them up automatically.

SUPPORTED_MODELS: list[ModelInfo] = [

    # ── ANTHROPIC / CLAUDE ──────────────────────────────────────────────────
    ModelInfo(
        model_id="claude-opus-4-6",
        display_name="Claude Opus 4.6",
        provider=ModelProvider.ANTHROPIC,
        context_window=200_000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
    ),
    ModelInfo(
        model_id="claude-sonnet-4-6",
        display_name="Claude Sonnet 4.6",
        provider=ModelProvider.ANTHROPIC,
        context_window=200_000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    ),
    ModelInfo(
        model_id="claude-haiku-4-5-20251001",
        display_name="Claude Haiku 4.5",
        provider=ModelProvider.ANTHROPIC,
        context_window=200_000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
    ),

    # ── OPENAI ───────────────────────────────────────────────────────────────
    ModelInfo(
        model_id="gpt-4o",
        display_name="GPT-4o",
        provider=ModelProvider.OPENAI,
        context_window=128_000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
    ),
    ModelInfo(
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        provider=ModelProvider.OPENAI,
        context_window=128_000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    ),
    ModelInfo(
        model_id="o3-mini",
        display_name="o3-mini (Reasoning)",
        provider=ModelProvider.OPENAI,
        context_window=200_000,
        supports_tools=True,
        supports_vision=False,
        supports_streaming=True,
        cost_per_1k_input=0.0011,
        cost_per_1k_output=0.0044,
    ),

    # ── GOOGLE GEMINI ────────────────────────────────────────────────────────
    ModelInfo(
        model_id="gemini/gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        provider=ModelProvider.GOOGLE,
        context_window=1_000_000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0004,
    ),
    ModelInfo(
        model_id="gemini/gemini-2.0-flash-thinking-exp",
        display_name="Gemini 2.0 Flash Thinking",
        provider=ModelProvider.GOOGLE,
        context_window=1_000_000,
        supports_tools=False,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
    ),

    # ── DEEPSEEK ─────────────────────────────────────────────────────────────
    ModelInfo(
        model_id="deepseek/deepseek-chat",
        display_name="DeepSeek Chat (V3)",
        provider=ModelProvider.DEEPSEEK,
        context_window=64_000,
        supports_tools=True,
        supports_vision=False,
        supports_streaming=True,
        cost_per_1k_input=0.00027,
        cost_per_1k_output=0.0011,
    ),
    ModelInfo(
        model_id="deepseek/deepseek-reasoner",
        display_name="DeepSeek R1 (Reasoner)",
        provider=ModelProvider.DEEPSEEK,
        context_window=64_000,
        supports_tools=False,
        supports_vision=False,
        supports_streaming=True,
        cost_per_1k_input=0.00055,
        cost_per_1k_output=0.00219,
    ),
]

# Fast lookup by model_id
_MODEL_MAP: dict[str, ModelInfo] = {m.model_id: m for m in SUPPORTED_MODELS}


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=ModelListResponse,
    summary="List all supported models",
    description="Returns every model the platform supports via LiteLLM, "
                "grouped with provider, context window, and pricing info.",
)
async def list_models(
    provider: ModelProvider | None = None,
    supports_tools: bool | None = None,
    supports_vision: bool | None = None,
    _user=Depends(get_current_user),
) -> ModelListResponse:
    """
    Optional query filters:
    - ?provider=anthropic
    - ?supports_tools=true
    - ?supports_vision=true
    """
    filtered = SUPPORTED_MODELS

    if provider:
        filtered = [m for m in filtered if m.provider == provider]
    if supports_tools is not None:
        filtered = [m for m in filtered if m.supports_tools == supports_tools]
    if supports_vision is not None:
        filtered = [m for m in filtered if m.supports_vision == supports_vision]

    return ModelListResponse(
        models=filtered,
        default_model=settings.DEFAULT_MODEL,
    )


@router.get(
    "/providers",
    summary="List model providers",
    description="Returns distinct providers and how many models each has.",
)
async def list_providers(_user=Depends(get_current_user)):
    from collections import defaultdict
    provider_counts: dict[str, int] = defaultdict(int)
    for model in SUPPORTED_MODELS:
        provider_counts[model.provider.value] += 1

    return {
        "providers": [
            {"provider": p, "model_count": c}
            for p, c in sorted(provider_counts.items())
        ]
    }


@router.get(
    "/{model_id:path}",
    response_model=ModelInfo,
    summary="Get single model info",
    description="Returns full metadata for one model. "
                "model_id must be URL-encoded if it contains slashes "
                "(e.g. 'gemini%2Fgemini-2.0-flash').",
)
async def get_model(
    model_id: str,
    _user=Depends(get_current_user),
) -> ModelInfo:
    model = _MODEL_MAP.get(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found. "
                   f"Call GET /models to see supported models."
        )
    return model


@router.post(
    "/validate",
    response_model=ModelValidateResponse,
    summary="Validate / ping a model",
    description="Sends a 1-token test completion to verify the model "
                "is reachable and the API key works. "
                "Use this before starting a session with an unfamiliar model.",
)
async def validate_model(
    body: ModelValidateRequest,
    _user=Depends(get_current_user),
) -> ModelValidateResponse:
    """
    Optionally pass your own api_key in the body to test a
    user-supplied key (e.g. bring-your-own-key flows).
    """
    import litellm

    # If user passes their own key, set it just for this call
    extra_kwargs = {}
    if body.api_key:
        extra_kwargs["api_key"] = body.api_key

    try:
        start = time.monotonic()
        await litellm.acompletion(
            model=body.model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            **extra_kwargs,
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        return ModelValidateResponse(
            model=body.model,
            is_valid=True,
            latency_ms=latency_ms,
        )
    except litellm.exceptions.AuthenticationError:
        return ModelValidateResponse(
            model=body.model,
            is_valid=False,
            error="Authentication failed — check your API key.",
        )
    except litellm.exceptions.NotFoundError:
        return ModelValidateResponse(
            model=body.model,
            is_valid=False,
            error=f"Model '{body.model}' not found or not accessible.",
        )
    except Exception as e:
        return ModelValidateResponse(
            model=body.model,
            is_valid=False,
            error=str(e),
        )