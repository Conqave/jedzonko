from abc import ABC, abstractmethod
from datetime import datetime

from catalog.domain.ingredient_line import LineInterpretation


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

    @abstractmethod
    def reassign(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        raise NotImplementedError
