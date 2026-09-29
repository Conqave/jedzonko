from abc import ABC, abstractmethod
from datetime import datetime

from recipes.domain.external_line import LineInterpretation


class IngredientLineRepository(ABC):
    @abstractmethod
    def find_interpretations(
        self, normalized_texts: tuple[str, ...]
    ) -> dict[str, LineInterpretation]:
        raise NotImplementedError

    @abstractmethod
    def save_interpretations(
        self,
        interpretations: dict[str, LineInterpretation],
        model_name: str,
        interpreted_at: datetime,
    ) -> None:
        raise NotImplementedError
