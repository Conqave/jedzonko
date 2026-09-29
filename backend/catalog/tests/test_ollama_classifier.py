import json
from collections.abc import Callable

import httpx
import pytest

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.infrastructure.providers.ollama.classifier import OllamaIngredientClassifier
from shared.infrastructure.ollama_chat import OllamaChat, OllamaSettings

INGREDIENTS = ("maślanka", "jajka", "skyr")


def _classifier(handler: Callable[[httpx.Request], httpx.Response]) -> OllamaIngredientClassifier:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    settings = OllamaSettings("http://192.0.2.1:11434/", "gpt-oss:20b", "high", 10, 256)
    return OllamaIngredientClassifier(OllamaChat(client, settings))


def _answer(content: str) -> httpx.Response:
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


def test_a_numbered_answer_selects_the_ingredient() -> None:
    classifier = _classifier(lambda request: _answer("2"))

    assert classifier.find_matching_ingredient("Jaja ściółkowe", INGREDIENTS) == 1


def test_zero_means_no_ingredient_fits() -> None:
    classifier = _classifier(lambda request: _answer("0"))

    assert classifier.find_matching_ingredient("Folia aluminiowa", INGREDIENTS) is None


def test_the_request_numbers_every_ingredient_and_names_the_model() -> None:
    seen: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(body)
        return _answer("0")

    classifier = _classifier(handler)
    classifier.find_matching_ingredient("Jaja", INGREDIENTS)

    body = seen[0]
    assert body["model"] == "gpt-oss:20b"
    assert body["think"] == "high"
    messages = body["messages"]
    assert isinstance(messages, list)
    prompt = messages[0]["content"]
    assert "Produkt: Jaja" in prompt
    assert "1. maślanka\n2. jajka\n3. skyr" in prompt


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500),
        httpx.Response(404),
    ],
)
def test_an_http_failure_means_the_model_is_unavailable(response: httpx.Response) -> None:
    classifier = _classifier(lambda request: response)

    with pytest.raises(IngredientClassifierUnavailableError):
        classifier.find_matching_ingredient("Jaja", INGREDIENTS)


def test_a_connection_failure_means_the_model_is_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    classifier = _classifier(handler)

    with pytest.raises(IngredientClassifierUnavailableError):
        classifier.find_matching_ingredient("Jaja", INGREDIENTS)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not json"),
        httpx.Response(200, json={"message": {}}),
        httpx.Response(200, json=[]),
        _answer("maybe the second one"),
        _answer("7"),
    ],
)
def test_an_answer_breaking_the_contract_is_rejected(response: httpx.Response) -> None:
    classifier = _classifier(lambda request: response)

    with pytest.raises(IngredientClassifierContractError):
        classifier.find_matching_ingredient("Jaja", INGREDIENTS)
