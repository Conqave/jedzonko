from abc import ABC, abstractmethod

from catalog.domain.ingredient import Ingredient
from catalog.domain.ingredient_line import LineInterpretation


class IngredientLineInterpreter(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def interpret(
        self, lines: tuple[str, ...], tags: tuple[Ingredient, ...]
    ) -> tuple[LineInterpretation, ...]:
        raise NotImplementedError
