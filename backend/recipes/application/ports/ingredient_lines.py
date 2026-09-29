from abc import ABC, abstractmethod
from datetime import datetime

from recipes.domain.external_line import LineInterpretation


class IngredientLines(ABC):
    @abstractmethod
    def find_interpretations(self, texts: tuple[str, ...]) -> dict[str, LineInterpretation]:
        raise NotImplementedError

    @abstractmethod
    def interpret(self, texts: tuple[str, ...], now: datetime) -> int:
        raise NotImplementedError
