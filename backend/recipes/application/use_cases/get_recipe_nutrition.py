from recipes.application.errors import RecipeNotFoundError
from recipes.application.ports.ingredient_nutrition_facts import IngredientNutritionFacts
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.nutrition import (
    RecipeNutrition,
    list_tagged_ingredient_ids,
    summarize_nutrition,
)


class GetRecipeNutrition:
    def __init__(
        self, repository: RecipeRepository, nutrition_facts: IngredientNutritionFacts
    ) -> None:
        self._repository = repository
        self._nutrition_facts = nutrition_facts

    def execute(self, recipe_id: int) -> RecipeNutrition:
        recipe = self._repository.find_recipe(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError
        requirements = self._repository.list_requirements(recipe_id)
        ingredient_ids = list_tagged_ingredient_ids(requirements)
        facts = self._nutrition_facts.find_nutrition_facts(ingredient_ids)
        return summarize_nutrition(requirements, facts, recipe.summary.servings)
