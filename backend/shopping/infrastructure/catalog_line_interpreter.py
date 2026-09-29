from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime

from catalog.application.errors import IngredientClassifierError
from catalog.application.use_cases.interpret_ingredient_lines import InterpretIngredientLines
from shopping.application.errors import TaggingUnavailableError
from shopping.application.ports.line_interpreter import LineInterpreter
from shopping.domain.line_meaning import LineMeaning


class CatalogLineInterpreter(LineInterpreter):
    def __init__(
        self, open_interpretation: Callable[[], AbstractContextManager[InterpretIngredientLines]]
    ) -> None:
        self._open_interpretation = open_interpretation

    def interpret(self, texts: tuple[str, ...], now: datetime) -> dict[str, LineMeaning]:
        try:
            with self._open_interpretation() as interpretation:
                run = interpretation.execute(texts, now)
        except IngredientClassifierError as error:
            raise TaggingUnavailableError(str(error)) from error
        return {
            text: LineMeaning(
                ingredient_id=line.ingredient_id, quantity=line.quantity, unit_code=line.unit_code
            )
            for text, line in run.interpretations.items()
        }
