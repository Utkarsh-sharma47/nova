"""LLM factory for query intent classification (never executes SQL)."""

from __future__ import annotations

import logging

from nova.llm.mock import MockLLM
from nova.llm.port import LLMPort, LLMRequest

logger = logging.getLogger("nova.query.llm")


def _default_unsupported(_request: LLMRequest) -> dict[str, object]:
    return {"name": "unsupported", "parameters": {}, "confidence": 0.0}


def build_query_llm(provider: str, model: str | None, api_key: str | None) -> LLMPort:
    """Mock by default: unknown questions become UNSUPPORTED, not invented answers."""
    del api_key
    if provider.lower() in {"mock", "test", "none", ""}:
        return MockLLM(
            factory=_default_unsupported,
            model=model or "mock-query-intent-v1",
        )
    logger.warning(
        "unsupported_query_llm_provider_falling_back_to_mock",
        extra={
            "event": "query.llm.provider_fallback",
            "extra_fields": {"provider": provider},
        },
    )
    return MockLLM(factory=_default_unsupported, model=model or "mock-query-intent-v1")
