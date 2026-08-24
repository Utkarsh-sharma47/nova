"""Deterministic MockLLM for tests and evaluation (no network)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from nova.llm.errors import LLMError, LLMProviderError
from nova.llm.port import LLMRequest, LLMResponse

ResponseFactory = Callable[[LLMRequest], str | LLMResponse | Exception]


class MockLLM:
    """Queue- or factory-backed LLM stub.

    Default test/eval environment must not require real API keys.
    """

    def __init__(
        self,
        *,
        responses: Sequence[str | LLMResponse | Exception | ResponseFactory] | None = None,
        provider: str = "mock",
        model: str = "mock-extractor-v1",
        default_factory: ResponseFactory | None = None,
    ) -> None:
        self._queue: list[str | LLMResponse | Exception | ResponseFactory] = list(
            responses or []
        )
        self._provider = provider
        self._model = model
        self._default_factory = default_factory
        self.calls: list[LLMRequest] = []

    def push(self, item: str | LLMResponse | Exception | ResponseFactory) -> None:
        self._queue.append(item)

    def clear(self) -> None:
        self._queue.clear()
        self.calls.clear()

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls.append(request)
        if self._queue:
            item = self._queue.pop(0)
        elif self._default_factory is not None:
            item = self._default_factory
        else:
            raise LLMProviderError(
                "MockLLM has no queued responses",
                retryable=False,
                code="MOCK_EMPTY",
            )

        if callable(item):
            produced = item(request)
            item = produced

        if isinstance(item, Exception):
            if isinstance(item, LLMError):
                raise item
            raise LLMProviderError(str(item), retryable=False) from item

        if isinstance(item, LLMResponse):
            return item

        content = str(item)
        return LLMResponse(
            content=content,
            provider=self._provider,
            model=self._model,
            input_tokens=_approx_tokens(request),
            output_tokens=max(1, len(content) // 4),
            raw={"source": "mock_queue"},
        )


def _approx_tokens(request: LLMRequest) -> int:
    total = sum(len(message.content) for message in request.messages)
    return max(1, total // 4)


def scripted_json_response(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload)
