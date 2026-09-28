from collections.abc import Callable

import httpx
import pytest

from households.application.ports.ingredient_matcher import (
    IngredientMatcherContractError,
    IngredientMatcherUnavailable,
)
from households.infrastructure.providers.ollama.matcher import OllamaIngredientMatcher

PRODUCTS = ("Maślanka naturalna", "Jaja ściółkowe (opakowanie)", "Skyr naturalny")


def _matcher(handler: Callable[[httpx.Request], httpx.Response]) -> OllamaIngredientMatcher:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaIngredientMatcher(client, "http://192.0.2.1:11434/", "gpt-oss:20b", "high")


def _answer(content: str) -> httpx.Response:
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


def test_a_numbered_answer_selects_the_product() -> None:
    matcher = _matcher(lambda request: _answer("2"))

    assert matcher.find_matching_product("jajko", PRODUCTS) == 1


def test_zero_means_the_pantry_holds_no_such_product() -> None:
    matcher = _matcher(lambda request: _answer("0"))

    assert matcher.find_matching_product("masło", PRODUCTS) is None


def test_the_prompt_numbers_every_product_and_asks_for_a_number() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.content.decode())
        return _answer("0")

    _matcher(handler).find_matching_product("jajko", PRODUCTS)

    assert "2. Jaja ściółkowe (opakowanie)" in seen[0]
    assert "gpt-oss:20b" in seen[0]
    assert "high" in seen[0]


def test_an_out_of_range_answer_is_a_contract_error() -> None:
    matcher = _matcher(lambda request: _answer("9"))

    with pytest.raises(IngredientMatcherContractError):
        matcher.find_matching_product("jajko", PRODUCTS)


def test_an_answer_without_a_number_is_a_contract_error() -> None:
    matcher = _matcher(lambda request: _answer("Jaja scielkowe"))

    with pytest.raises(IngredientMatcherContractError):
        matcher.find_matching_product("jajko", PRODUCTS)


def test_an_unreachable_host_is_reported_as_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(IngredientMatcherUnavailable):
        _matcher(handler).find_matching_product("jajko", PRODUCTS)
