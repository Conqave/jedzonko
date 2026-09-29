from abc import ABC, abstractmethod

from recipes.application.commands import RecipeInput, ResolvedIngredient
from recipes.domain.models import (
    RecipeCategory,
    RecipeDetail,
    RecipeRequirement,
    RecipeSummary,
)


class RecipeRepository(ABC):
    @abstractmethod
    def list_recipes(self) -> list[RecipeSummary]:
        raise NotImplementedError

    @abstractmethod
    def list_categories(self) -> list[RecipeCategory]:
        raise NotImplementedError

    @abstractmethod
    def find_recipe(self, recipe_id: int) -> RecipeDetail | None:
        raise NotImplementedError

    @abstractmethod
    def list_requirements(self, recipe_id: int) -> list[RecipeRequirement]:
        raise NotImplementedError

    @abstractmethod
    def list_requirements_by_recipe(self) -> dict[int, list[RecipeRequirement]]:
        raise NotImplementedError

    @abstractmethod
    def create_recipe(
        self,
        command: RecipeInput,
        ingredients: tuple[ResolvedIngredient, ...],
        created_by_user_id: int,
    ) -> RecipeDetail:
        raise NotImplementedError

    @abstractmethod
    def update_recipe(
        self, recipe_id: int, command: RecipeInput, ingredients: tuple[ResolvedIngredient, ...]
    ) -> RecipeDetail:
        raise NotImplementedError

    @abstractmethod
    def delete_recipe(self, recipe_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def reassign_ingredient(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        raise NotImplementedError
