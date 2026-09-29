import json
from decimal import Decimal, InvalidOperation

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.application.ports.ingredient_line_interpreter import IngredientLineInterpreter
from catalog.domain.ingredient import Ingredient
from catalog.domain.ingredient_line import LineInterpretation
from catalog.infrastructure.providers.ollama.line_prompt import (
    build_line_prompt,
    build_line_schema,
)
from shared.infrastructure.ollama_chat import (
    OllamaChat,
    OllamaContractError,
    OllamaUnavailableError,
)
from shared.measurement_units import find_measurement_unit

_QUANTITY_LIMIT = Decimal("1000000000")


class OllamaIngredientLineInterpreter(IngredientLineInterpreter):
    def __init__(self, chat: OllamaChat) -> None:
        self._chat = chat

    @property
    def model_name(self) -> str:
        return self._chat.model_name

    def interpret(
        self, lines: tuple[str, ...], tags: tuple[Ingredient, ...]
    ) -> tuple[LineInterpretation, ...]:
        if not lines or not tags:
            raise ValueError("Interpreting needs lines and ingredient choices.")
        prompt = build_line_prompt(lines, tags)
        schema = build_line_schema()
        content = self._ask(prompt, schema)
        entries = _read_entries(content, len(lines))
        return tuple(_to_interpretation(entries[position], tags) for position in range(len(lines)))

    def _ask(self, prompt: str, schema: dict[str, object]) -> str:
        try:
            return self._chat.ask_structured(prompt, schema)
        except OllamaUnavailableError as error:
            raise IngredientClassifierUnavailableError(str(error)) from error
        except OllamaContractError as error:
            raise IngredientClassifierContractError(str(error)) from error


def _read_entries(content: str, line_count: int) -> dict[int, dict[str, object]]:
    try:
        body = json.loads(content)
    except json.JSONDecodeError as error:
        raise IngredientClassifierContractError("The model answer is not JSON.") from error
    entries = body.get("lines") if isinstance(body, dict) else None
    if not isinstance(entries, list):
        raise IngredientClassifierContractError("The model answer has no line list.")
    by_position: dict[int, dict[str, object]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise IngredientClassifierContractError("A line entry is not an object.")
        line = entry.get("line")
        if not isinstance(line, int) or isinstance(line, bool) or not 1 <= line <= line_count:
            raise IngredientClassifierContractError(f"Unknown line number {line!r}.")
        by_position[line - 1] = entry
    if len(by_position) != line_count:
        raise IngredientClassifierContractError("The model skipped some lines.")
    return by_position


def _to_interpretation(
    entry: dict[str, object], tags: tuple[Ingredient, ...]
) -> LineInterpretation:
    ingredient_id = _read_ingredient_id(entry["ingredient"], tags)
    quantity = _read_quantity(entry["quantity"])
    unit_code = _read_unit_code(entry["unit"])
    is_amount_complete = quantity is not None and unit_code is not None
    if not is_amount_complete:
        return LineInterpretation(ingredient_id=ingredient_id, quantity=None, unit_code=None)
    return LineInterpretation(ingredient_id=ingredient_id, quantity=quantity, unit_code=unit_code)


def _read_ingredient_id(value: object, tags: tuple[Ingredient, ...]) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= len(tags):
        raise IngredientClassifierContractError(f"Unknown ingredient number {value!r}.")
    if value == 0:
        return None
    return tags[value - 1].id


def _read_quantity(value: object) -> Decimal | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise IngredientClassifierContractError(f"Quantity {value!r} is not text.")
    try:
        quantity = Decimal(value.strip().replace(",", "."))
    except InvalidOperation as error:
        raise IngredientClassifierContractError(f"Quantity {value!r} is no number.") from error
    if not quantity.is_finite() or quantity <= 0:
        return None
    if quantity >= _QUANTITY_LIMIT:
        raise IngredientClassifierContractError(f"Quantity {value!r} is out of range.")
    return quantity.quantize(Decimal("0.001"))


def _read_unit_code(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or find_measurement_unit(value) is None:
        raise IngredientClassifierContractError(f"Unknown unit {value!r}.")
    return value
