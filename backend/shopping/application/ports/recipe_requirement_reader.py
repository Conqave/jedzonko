from abc import ABC, abstractmethod

from shopping.domain.missing_recipe_item import MissingRecipeItem


class RecipeRequirementReader(ABC):
    @abstractmethod
    def read_missing_items(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> list[MissingRecipeItem]:
        raise NotImplementedError
