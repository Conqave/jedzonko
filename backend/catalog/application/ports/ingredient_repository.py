from abc import ABC, abstractmethod

from catalog.domain.ingredient import (
    Ingredient,
    IngredientName,
    IngredientNameKind,
    IngredientNameSource,
)
from catalog.domain.names import IngredientNameText


class IngredientRepository(ABC):
    @abstractmethod
    def find(self, ingredient_id: int) -> Ingredient | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_normalized_name(self, normalized_name: str) -> Ingredient | None:
        """Exact lookup among accepted ingredient names only."""
        raise NotImplementedError

    @abstractmethod
    def create(self, name: IngredientNameText, source: IngredientNameSource) -> Ingredient:
        """Create the ingredient together with its canonical name."""
        raise NotImplementedError

    @abstractmethod
    def add_name(
        self,
        ingredient_id: int,
        name: IngredientNameText,
        kind: IngredientNameKind,
        source: IngredientNameSource,
    ) -> IngredientName:
        raise NotImplementedError
