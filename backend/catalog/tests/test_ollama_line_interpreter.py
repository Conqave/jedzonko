import json
from collections.abc import Callable
from decimal import Decimal

import httpx
import pytest

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.domain.ingredient import Ingredient
from catalog.domain.ingredient_line import LineInterpretation
from catalog.infrastructure.providers.ollama.line_interpreter import (
    INTERPRETATION_OUTPUT_TOKENS,
    OllamaIngredientLineInterpreter,
)
from shared.infrastructure.ollama_chat import OllamaChat, OllamaSettings

CHOICES = (
    Ingredient(id=11, name="jajko", calories=None),
    Ingredient(id=22, name="mleko", calories=None),
)
LINES = ("3 średnie jajka", "szklanka mleka", "szczypta soli")


def _interpreter(
    handler: Callable[[httpx.Request], httpx.Response],
) -> OllamaIngredientLineInterpreter:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = OllamaSettings(
        "http://192.0.2.1:11434", "gpt-oss:20b-128k", "medium", 10, 2048, 98304, 131072
    )
    return OllamaIngredientLineInterpreter(OllamaChat(client, settings))


def _answer(entries: list[dict[str, object]]) -> httpx.Response:
    content = json.dumps({"lines": entries})
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


ENTRIES: list[dict[str, object]] = [
    {"line": 1, "ingredient": 1, "quantity": "3", "unit": "szt"},
    {"line": 2, "ingredient": 2, "quantity": None, "unit": None},
    {"line": 3, "ingredient": 0, "quantity": None, "unit": None},
]


def test_numbers_become_ingredient_ids_and_amounts() -> None:
    interpreter = _interpreter(lambda request: _answer(ENTRIES))

    interpreted = interpreter.interpret(LINES, CHOICES)

    assert interpreted == (
        LineInterpretation(ingredient_id=11, quantity=Decimal("3.000"), unit_code="szt"),
        LineInterpretation(ingredient_id=22, quantity=None, unit_code=None),
        LineInterpretation(ingredient_id=None, quantity=None, unit_code=None),
    )


def test_the_request_is_structured_bounded_and_lists_every_line() -> None:
    seen: list[dict[str, object]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return _answer(ENTRIES)

    _interpreter(handle).interpret(LINES, CHOICES)

    body = seen[0]
    prompt = json.dumps(body["messages"], ensure_ascii=False)
    assert body["model"] == "gpt-oss:20b-128k"
    assert body["options"] == {"num_predict": INTERPRETATION_OUTPUT_TOKENS, "num_ctx": 98304}
    assert isinstance(body["format"], dict)
    assert "1. jajko" in prompt and "3. szczypta soli" in prompt


def test_an_amount_without_a_unit_is_no_amount() -> None:
    entries = [dict(ENTRIES[0], unit=None), ENTRIES[1], ENTRIES[2]]
    interpreter = _interpreter(lambda request: _answer(entries))

    interpreted = interpreter.interpret(LINES, CHOICES)

    assert interpreted[0] == LineInterpretation(ingredient_id=11, quantity=None, unit_code=None)


@pytest.mark.parametrize(
    "entries",
    [
        ENTRIES[:2],
        [ENTRIES[0], ENTRIES[1], dict(ENTRIES[2], ingredient=7)],
        [ENTRIES[0], ENTRIES[1], dict(ENTRIES[2], line=9)],
        [dict(ENTRIES[0], unit="szklanka"), ENTRIES[1], ENTRIES[2]],
        [dict(ENTRIES[0], quantity="trzy"), ENTRIES[1], ENTRIES[2]],
    ],
)
def test_an_answer_breaking_the_contract_is_rejected(entries: list[dict[str, object]]) -> None:
    interpreter = _interpreter(lambda request: _answer(entries))

    with pytest.raises(IngredientClassifierContractError):
        interpreter.interpret(LINES, CHOICES)


def test_an_unreachable_model_is_unavailable() -> None:
    interpreter = _interpreter(lambda request: httpx.Response(503))

    with pytest.raises(IngredientClassifierUnavailableError):
        interpreter.interpret(LINES, CHOICES)
