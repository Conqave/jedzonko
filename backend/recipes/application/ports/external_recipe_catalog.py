from abc import ABC, abstractmethod
from datetime import datetime

from recipes.domain.external import ExternalRecipeIngredient, ImportedExternalRecipe, RecipeImage


class ExternalRecipeCatalog(ABC):
    @abstractmethod
    def list_references(self) -> frozenset[str]:
        raise NotImplementedError

    @abstractmethod
    def list_missing_images(self) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def find_ingredients(self, reference: str) -> tuple[ExternalRecipeIngredient, ...] | None:
        raise NotImplementedError

    @abstractmethod
    def find_image_urls(self, references: tuple[str, ...]) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def list_ingredient_texts(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def save_recipe(
        self, recipe: ImportedExternalRecipe, image: RecipeImage | None, fetched_at: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_image(self, reference: str, image: RecipeImage) -> None:
        raise NotImplementedError
