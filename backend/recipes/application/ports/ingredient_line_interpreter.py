from abc import ABC, abstractmethod

from recipes.domain.external_line import IngredientChoice, LineInterpretation


class IngredientLineInterpreter(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def interpret(
        self, lines: tuple[str, ...], choices: tuple[IngredientChoice, ...]
    ) -> tuple[LineInterpretation, ...]:
        raise NotImplementedError
