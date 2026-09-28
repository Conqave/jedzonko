from abc import ABC, abstractmethod

from recipes.domain.external import ExternalRecipeDetail, ExternalRecipePage


class RecipeSourceError(Exception):
    pass


class RecipeSourceUnavailableError(RecipeSourceError):
    pass


class RecipeSourceContractError(RecipeSourceError):
    pass


class RecipeNotFoundAtSourceError(RecipeSourceError):
    pass


class RecipeSource(ABC):
    @abstractmethod
    def get_recipe(self, reference: str) -> ExternalRecipeDetail:
        raise NotImplementedError

    @abstractmethod
    def search_recipes(
        self,
        query: str,
        ingredient_names: tuple[str, ...],
        excluded_ingredient_names: tuple[str, ...],
        page: int,
        page_size: int,
    ) -> ExternalRecipePage:
        raise NotImplementedError
