"""OpenAI-compatible adapter unit tests (no live network)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from nova.application.extraction import build_default_llm
from nova.llm.errors import LLMProviderError
from nova.llm.mock import MockLLM
from nova.llm.openai_compatible import OpenAICompatibleLLM, _to_openai_messages
from nova.llm.port import LLMImagePart, LLMMessage, LLMRequest


def test_build_default_llm_falls_back_without_api_key() -> None:
    llm = build_default_llm("openai", "gpt-4o-mini", None)
    assert isinstance(llm, MockLLM)


def test_build_default_llm_wires_openai_when_key_present() -> None:
    llm = build_default_llm("openai", "gpt-4o-mini", "sk-test")
    assert isinstance(llm, OpenAICompatibleLLM)


def test_openai_messages_include_image_parts() -> None:
    request = LLMRequest(
        messages=[
            LLMMessage(role="system", content="sys"),
            LLMMessage(role="user", content="extract"),
        ],
        images=[LLMImagePart(media_type="image/png", data_base64="abc123")],
    )
    messages = _to_openai_messages(request)
    assert messages[0]["content"] == "sys"
    assert isinstance(messages[1]["content"], list)
    assert messages[1]["content"][0]["type"] == "text"
    assert messages[1]["content"][1]["type"] == "image_url"
    assert "data:image/png;base64,abc123" in messages[1]["content"][1]["image_url"]["url"]


def test_openai_complete_parses_response() -> None:
    payload = {
        "model": "gpt-4o-mini",
        "choices": [{"message": {"content": '{"fields":[]}'}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response) as mocked:
        llm = OpenAICompatibleLLM(api_key="sk-test", model="gpt-4o-mini")
        result = llm.complete(
            LLMRequest(messages=[LLMMessage(role="user", content="hi")], timeout_ms=5_000)
        )
    assert result.content == '{"fields":[]}'
    assert result.input_tokens == 10
    assert mocked.called


def test_openai_http_error_maps_to_provider_error() -> None:
    import urllib.error

    error = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=401,
        msg="Unauthorized",
        hdrs=None,  # type: ignore[arg-type]
        fp=MagicMock(read=MagicMock(return_value=b'{"error":"bad"}')),
    )
    with patch("urllib.request.urlopen", side_effect=error):
        llm = OpenAICompatibleLLM(api_key="sk-bad")
        with pytest.raises(LLMProviderError):
            llm.complete(LLMRequest(messages=[LLMMessage(role="user", content="hi")]))


def test_openai_requires_api_key() -> None:
    with pytest.raises(ValueError):
        OpenAICompatibleLLM(api_key="  ")
