"""
core/token_counter.py — Token Counting Utilities
=================================================
Accurate token counting for context budget management.
Uses tiktoken (OpenAI tokenizer) as the baseline — it's close enough
for all models and avoids importing multiple tokenizer libraries.

For Claude specifically, Anthropic's tokenizer is slightly different
but within ~5% of tiktoken counts, which is acceptable for budgeting.
"""

import tiktoken
from functools import lru_cache
from typing import Union
import structlog

log = structlog.get_logger(__name__)

# cl100k_base is used by GPT-4, Claude (approx), Gemini (approx)
_ENCODING_NAME = "cl100k_base"


@lru_cache(maxsize=1)
def _get_encoder():
    try:
        return tiktoken.get_encoding(_ENCODING_NAME)
    except Exception as e:
        log.warning("token_counter.fallback", error=str(e))
        return None


def count_tokens(text: str) -> int:
    """
    Count tokens in a string.
    Falls back to word-based estimate if tiktoken unavailable.
    """
    if not text:
        return 0

    encoder = _get_encoder()
    if encoder:
        try:
            return len(encoder.encode(text))
        except Exception:
            pass

    # Rough fallback: ~1.3 tokens per word
    return int(len(text.split()) * 1.3)


def count_messages_tokens(messages: list[dict]) -> int:
    """
    Count tokens across a list of message dicts.
    Accounts for role tokens and message overhead (~4 tokens per message).
    """
    total = 0
    for msg in messages:
        total += 4  # message overhead
        content = msg.get("content", "")
        if isinstance(content, str):
            total += count_tokens(content)
        elif isinstance(content, list):
            # Multi-part content (tool_use, tool_result, images)
            for part in content:
                if isinstance(part, dict):
                    total += count_tokens(str(part.get("content", "")))
                    total += count_tokens(str(part.get("text", "")))
    return total


def estimate_tool_tokens(tools: list[dict]) -> int:
    """
    Estimate tokens used by the tool schema definitions
    injected into every prompt.
    """
    import json
    tools_str = json.dumps(tools)
    return count_tokens(tools_str)


class TokenBudgetManager:
    """
    Tracks token budget across layers and makes allocation decisions.

    Layers (in priority order — higher priority = allocated first):
      1. system_prompt   — base instructions
      2. tools           — tool schema definitions
      3. user_message    — current user input
      4. skills          — injected skill content (RAG chunks)
      5. history         — conversation history (trimmed if needed)
      6. output_reserve  — always kept free for LLM response
    """

    def __init__(self, model: str, context_limit: int, output_reserve: int = 8192):
        self.model = model
        self.context_limit = context_limit
        self.output_reserve = output_reserve
        self.available = context_limit - output_reserve
        self.allocations: dict[str, int] = {}

    def allocate(self, layer: str, tokens: int) -> int:
        """
        Allocate tokens for a layer.
        Returns how many tokens were actually allocated (may be less than requested).
        """
        remaining = self.available - sum(self.allocations.values())
        allocated = min(tokens, remaining)
        self.allocations[layer] = allocated
        return allocated

    def remaining(self) -> int:
        return self.available - sum(self.allocations.values())

    def summary(self) -> dict:
        total_used = sum(self.allocations.values())
        return {
            "context_limit": self.context_limit,
            "output_reserve": self.output_reserve,
            "available_for_input": self.available,
            "total_used": total_used,
            "remaining": self.available - total_used,
            "utilization_pct": round((total_used / self.available) * 100, 1),
            "by_layer": self.allocations,
        }

    def can_fit(self, tokens: int) -> bool:
        return self.remaining() >= tokens

    def trim_history_to_fit(
        self,
        messages: list[dict],
        target_tokens: int,
    ) -> list[dict]:
        """
        Trim oldest messages to fit within target_tokens.
        Always keeps the first system message and the last user message.
        Removes from oldest (index 1) forward.
        """
        if count_messages_tokens(messages) <= target_tokens:
            return messages

        result = list(messages)
        while len(result) > 2 and count_messages_tokens(result) > target_tokens:
            # Remove second message (keep system first, user last)
            result.pop(1)

        return result
