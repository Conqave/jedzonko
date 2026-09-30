from abc import ABC, abstractmethod

from recipes.domain.external import ImportedExternalRecipe, RecipeImage


class RecipeSite(ABC):
    @abstractmethod
    def list_recipe_references(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def fetch_recipe(self, reference: str) -> ImportedExternalRecipe:
        raise NotImplementedError

    @abstractmethod
    def fetch_image(self, reference: str, url: str) -> RecipeImage:
        raise NotImplementedError
