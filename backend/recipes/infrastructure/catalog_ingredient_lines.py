from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.application.use_cases.find_ingredient_lines import FindIngredientLines
from catalog.application.use_cases.interpret_ingredient_lines import InterpretIngredientLines
from catalog.domain.ingredient_line import LineInterpretation as CatalogLine
from recipes.application.errors import (
    IngredientLineInterpreterContractError,
    IngredientLineInterpreterUnavailableError,
)
from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.domain.external_line import LineInterpretation


class CatalogIngredientLines(IngredientLines):
    def __init__(
        self,
        find_lines: FindIngredientLines,
        open_interpretation: Callable[[], AbstractContextManager[InterpretIngredientLines]],
    ) -> None:
        self._find_lines = find_lines
        self._open_interpretation = open_interpretation

    def find_interpretations(self, texts: tuple[str, ...]) -> dict[str, LineInterpretation]:
        found = self._find_lines.execute(texts)
        return {text: _to_recipe_line(line) for text, line in found.items()}

    def interpret(self, texts: tuple[str, ...], now: datetime) -> int:
        try:
            with self._open_interpretation() as interpretation:
                run = interpretation.execute(texts, now)
        except IngredientClassifierUnavailableError as error:
            raise IngredientLineInterpreterUnavailableError(str(error)) from error
        except IngredientClassifierContractError as error:
            raise IngredientLineInterpreterContractError(str(error)) from error
        return run.interpreted_count


def _to_recipe_line(line: CatalogLine) -> LineInterpretation:
    return LineInterpretation(
        ingredient_id=line.ingredient_id, quantity=line.quantity, unit_code=line.unit_code
    )
