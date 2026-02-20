"""
schemas/models.py — Pydantic request/response schemas
======================================================
Single source of truth for all request/response shapes.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Any
from enum import Enum
import uuid


# ─── ENUMS ───────────────────────────────────────────────────────────────────

class ModelProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI    = "openai"
    GOOGLE    = "google"
    DEEPSEEK  = "deepseek"


class MessageRole(str, Enum):
    USER      = "user"
    ASSISTANT = "assistant"
    SYSTEM    = "system"
    TOOL      = "tool"


class ToolApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT  = "reject"


class SkillFileType(str, Enum):
    MARKDOWN = "md"
    YAML     = "yml"
    YAML_ALT = "yaml"


# ─── MESSAGE SCHEMAS ─────────────────────────────────────────────────────────

class Message(BaseModel):
    role: MessageRole
    content: str
    name: Optional[str] = None          # for tool messages
    tool_call_id: Optional[str] = None  # for tool result messages


# ─── CHAT SCHEMAS ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Session ID. Auto-generated if not provided."
    )
    model: str = Field(
        default="claude-sonnet-4-6",
        description="LiteLLM model string e.g. 'gpt-4o', 'gemini/gemini-2.0-flash'"
    )
    messages: list[Message] = Field(
        ...,
        min_length=1,
        description="Conversation history. Last message must be role=user."
    )
    skill_ids: list[str] = Field(
        default=[],
        description="List of skill IDs to inject into this request's context."
    )
    stream: bool = Field(
        default=True,
        description="Stream tokens via SSE."
    )
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int]   = Field(default=None, ge=1, le=128000)
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional extra system instructions appended after skill content."
    )

    @validator("messages")
    def last_message_must_be_user(cls, v):
        if v and v[-1].role != MessageRole.USER:
            raise ValueError("Last message in messages list must have role='user'.")
        return v


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    model: str
    usage: dict[str, int]           # prompt_tokens, completion_tokens, total_tokens
    tool_calls_made: list[str]      # names of tools that were called
    skills_injected: list[str]      # skill IDs that were injected
    tokens_by_layer: dict[str, int] # breakdown: system, history, skills, user


class StreamChunk(BaseModel):
    type: Literal["token", "tool_start", "tool_result", "error", "done"]
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[Any] = None
    error: Optional[str] = None
    usage: Optional[dict[str, int]] = None


# ─── SESSION SCHEMAS ─────────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    model: str = Field(default="claude-sonnet-4-6")
    system_prompt: Optional[str] = None
    skill_ids: list[str] = Field(default=[])
    metadata: dict[str, Any] = Field(default={})


class SessionResponse(BaseModel):
    session_id: str
    model: str
    created_at: str
    updated_at: str
    message_count: int
    loaded_skill_ids: list[str]
    token_usage_total: int
    metadata: dict[str, Any]


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


# ─── SKILL SCHEMAS ───────────────────────────────────────────────────────────

class SkillMetadata(BaseModel):
    skill_id: str
    name: str
    description: Optional[str] = None
    file_type: SkillFileType
    file_name: str
    token_count: int
    section_count: int
    triggers: list[str] = []           # keywords that auto-activate this skill
    created_at: str
    is_embedded: bool = False          # True once added to FAISS index


class SkillUploadResponse(BaseModel):
    skill_id: str
    name: str
    file_name: str
    file_type: SkillFileType
    token_count: int
    section_count: int
    message: str


class SkillListResponse(BaseModel):
    skills: list[SkillMetadata]
    total: int
    total_tokens: int


class SkillSearchResult(BaseModel):
    skill_id: str
    skill_name: str
    section_title: str
    content: str
    similarity_score: float
    token_count: int


class SkillSearchResponse(BaseModel):
    query: str
    results: list[SkillSearchResult]
    total_tokens: int


# ─── MODEL SCHEMAS ───────────────────────────────────────────────────────────

class ModelInfo(BaseModel):
    model_id: str               # LiteLLM model string
    display_name: str
    provider: ModelProvider
    context_window: int         # max tokens
    supports_tools: bool
    supports_vision: bool
    supports_streaming: bool
    cost_per_1k_input: float    # USD
    cost_per_1k_output: float   # USD


class ModelListResponse(BaseModel):
    models: list[ModelInfo]
    default_model: str


class ModelValidateRequest(BaseModel):
    model: str
    api_key: Optional[str] = None   # user-provided key (optional override)


class ModelValidateResponse(BaseModel):
    model: str
    is_valid: bool
    latency_ms: Optional[int] = None
    error: Optional[str] = None


# ─── TOOL SCHEMAS ────────────────────────────────────────────────────────────

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]      # JSON schema
    requires_approval: bool = False
    is_enabled: bool = True
    category: str                   # "filesystem", "code", "web", "mcp"


class ToolListResponse(BaseModel):
    tools: list[ToolDefinition]
    total: int


class ToolApprovalRequest(BaseModel):
    session_id: str
    tool_call_id: str
    decision: ToolApprovalDecision
    reason: Optional[str] = None    # why rejected (shown to agent)


class ToolApprovalResponse(BaseModel):
    tool_call_id: str
    decision: ToolApprovalDecision
    message: str


class ToolToggleRequest(BaseModel):
    tool_name: str
    enabled: bool


# ─── HEALTH SCHEMAS ──────────────────────────────────────────────────────────

class ServiceStatus(BaseModel):
    name: str
    status: Literal["ok", "degraded", "down"]
    latency_ms: Optional[int] = None
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    services: list[ServiceStatus]
