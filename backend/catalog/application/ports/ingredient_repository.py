from abc import ABC, abstractmethod

from catalog.domain.ingredient import (
    Ingredient,
    IngredientName,
    IngredientNameKind,
    IngredientNameSource,
)
from catalog.domain.ingredient_search import IngredientNameMatch
from catalog.domain.names import CatalogName


class IngredientRepository(ABC):
    @abstractmethod
    def find(self, ingredient_id: int) -> Ingredient | None:
        raise NotImplementedError

    @abstractmethod
    def find_many(self, ingredient_ids: set[int]) -> dict[int, Ingredient]:
        raise NotImplementedError

    @abstractmethod
    def find_by_normalized_name(self, normalized_name: str) -> Ingredient | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_normalized_names(self, normalized_names: set[str]) -> dict[str, Ingredient]:
        raise NotImplementedError

    @abstractmethod
    def find_name_matches(self, normalized_query: str) -> list[IngredientNameMatch]:
        raise NotImplementedError

    @abstractmethod
    def list_names(self) -> list[IngredientName]:
        raise NotImplementedError

    @abstractmethod
    def create(self, name: CatalogName, source: IngredientNameSource) -> Ingredient:
        raise NotImplementedError

    @abstractmethod
    def add_name(
        self,
        ingredient_id: int,
        name: CatalogName,
        kind: IngredientNameKind,
        source: IngredientNameSource,
    ) -> IngredientName:
        raise NotImplementedError

    @abstractmethod
    def move_names_as_aliases(self, source_id: int, target_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def split_alias(self, normalized_name: str) -> Ingredient | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, ingredient_id: int) -> None:
        raise NotImplementedError
