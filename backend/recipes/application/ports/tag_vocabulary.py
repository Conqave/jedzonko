from abc import ABC, abstractmethod

from recipes.domain.external_line import IngredientChoice


class TagVocabulary(ABC):
    @abstractmethod
    def list_tags(self) -> tuple[IngredientChoice, ...]:
        raise NotImplementedError
