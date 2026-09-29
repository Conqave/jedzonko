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


def test_numbered_answers_select_every_matching_tag() -> None:
    classifier = _classifier(lambda request: _answer('{"tags": [3, 2, 3]}'))

    assert classifier.find_matching_tags("Jaja ściółkowe", INGREDIENTS) == (1, 2)


def test_an_empty_list_means_no_tag_fits() -> None:
    classifier = _classifier(lambda request: _answer('{"tags": []}'))

    assert classifier.find_matching_tags("Folia aluminiowa", INGREDIENTS) == ()


def test_the_request_numbers_every_ingredient_and_names_the_model() -> None:
    seen: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(body)
        return _answer('{"tags": []}')

    classifier = _classifier(handler)
    classifier.find_matching_tags("Jaja", INGREDIENTS)

    body = seen[0]
    assert body["model"] == "gpt-oss:20b"
    assert body["think"] == "high"
    messages = body["messages"]
    assert isinstance(messages, list)
    prompt = messages[0]["content"]
    assert "Produkt: Jaja" in prompt
    assert "1. maślanka\n2. jajka\n3. skyr" in prompt
    assert isinstance(body["format"], dict)
    assert body["options"] == {"num_predict": 256}


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
        classifier.find_matching_tags("Jaja", INGREDIENTS)


def test_a_connection_failure_means_the_model_is_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    classifier = _classifier(handler)

    with pytest.raises(IngredientClassifierUnavailableError):
        classifier.find_matching_tags("Jaja", INGREDIENTS)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not json"),
        httpx.Response(200, json={"message": {}}),
        httpx.Response(200, json=[]),
        _answer("maybe the second one"),
        _answer('{"tags": [7]}'),
        _answer('{"tags": "2"}'),
    ],
)
def test_an_answer_breaking_the_contract_is_rejected(response: httpx.Response) -> None:
    classifier = _classifier(lambda request: response)

    with pytest.raises(IngredientClassifierContractError):
        classifier.find_matching_tags("Jaja", INGREDIENTS)


def test_an_answer_cut_off_at_the_token_limit_is_rejected() -> None:
    body = {"message": {"role": "assistant", "content": '{"tags": ['}, "done_reason": "length"}
    classifier = _classifier(lambda request: httpx.Response(200, json=body))

    with pytest.raises(IngredientClassifierContractError, match="token limit"):
        classifier.find_matching_tags("Jaja", INGREDIENTS)
