from recipes.application.errors import RecipeNotFoundError
from recipes.application.ports.ingredient_calories import IngredientCalories
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.nutrition import (
    RecipeNutrition,
    list_tagged_ingredient_ids,
    summarize_nutrition,
)


class GetRecipeNutrition:
    def __init__(self, repository: RecipeRepository, calories: IngredientCalories) -> None:
        self._repository = repository
        self._calories = calories

    def execute(self, recipe_id: int) -> RecipeNutrition:
        recipe = self._repository.find_recipe(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError
        requirements = self._repository.list_requirements(recipe_id)
        ingredient_ids = list_tagged_ingredient_ids(requirements)
        kcal_per_100g = self._calories.find_kcal_per_100g(ingredient_ids)
        return summarize_nutrition(requirements, kcal_per_100g, recipe.summary.servings)
