import json

import httpx
import pytest

from shared.infrastructure.ollama_chat import (
    OllamaChat,
    OllamaContractError,
    OllamaSettings,
    estimate_tokens_upper_bound,
)

SCHEMA: dict[str, object] = {"type": "object"}
OUTPUT_TOKENS = 50
CONTEXT_TOKENS = 1000
MAX_CONTEXT_TOKENS = 2000


def _chat(sent: list[dict[str, object]]) -> OllamaChat:
    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "{}"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = OllamaSettings(
        "http://192.0.2.1:11434",
        "gpt-oss:20b-128k",
        "high",
        10,
        OUTPUT_TOKENS,
        CONTEXT_TOKENS,
        MAX_CONTEXT_TOKENS,
    )
    return OllamaChat(client, settings)


def _sent_context_tokens(payload: dict[str, object]) -> object:
    options = payload["options"]
    assert isinstance(options, dict)
    return options["num_ctx"]


def test_the_token_estimate_rounds_characters_up_by_three() -> None:
    assert estimate_tokens_upper_bound("abcd") == 2


def test_a_small_prompt_uses_the_gpu_context() -> None:
    sent: list[dict[str, object]] = []

    _chat(sent).ask_structured("Krótko.", SCHEMA)

    assert _sent_context_tokens(sent[0]) == CONTEXT_TOKENS


def test_a_large_prompt_uses_the_max_context() -> None:
    sent: list[dict[str, object]] = []

    _chat(sent).ask_structured("x" * 3000, SCHEMA)

    assert _sent_context_tokens(sent[0]) == MAX_CONTEXT_TOKENS


def test_the_max_context_stays_for_later_small_prompts() -> None:
    sent: list[dict[str, object]] = []
    chat = _chat(sent)

    chat.ask_structured("x" * 3000, SCHEMA)
    chat.ask_structured("Krótko.", SCHEMA)

    assert _sent_context_tokens(sent[1]) == MAX_CONTEXT_TOKENS


def test_a_prompt_above_the_max_context_is_not_sent() -> None:
    sent: list[dict[str, object]] = []

    with pytest.raises(OllamaContractError):
        _chat(sent).ask_structured("x" * 6000, SCHEMA)

    assert sent == []
