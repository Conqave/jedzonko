from abc import ABC, abstractmethod

from recipes.application.commands import RecipeInput
from recipes.domain.models import RecipeDetail, RecipeRequirement, RecipeSummary


class RecipeRepository(ABC):
    @abstractmethod
    def list_recipes(self) -> list[RecipeSummary]:
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
    def create_recipe(self, command: RecipeInput, created_by_user_id: int) -> RecipeDetail:
        raise NotImplementedError

    @abstractmethod
    def update_recipe(self, recipe_id: int, command: RecipeInput) -> RecipeDetail:
        raise NotImplementedError

    @abstractmethod
    def delete_recipe(self, recipe_id: int) -> None:
        raise NotImplementedError
