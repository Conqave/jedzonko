from recipes.application.external_requirements import read_external_requirements
from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.ingredient_calories import IngredientCalories
from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.nutrition import (
    RecipeNutrition,
    list_tagged_ingredient_ids,
    summarize_nutrition,
)


class GetExternalRecipeNutrition:
    def __init__(
        self,
        catalog: ExternalRecipeCatalog,
        source: RecipeSource,
        resolver: IngredientResolver,
        lines: IngredientLines,
        calories: IngredientCalories,
    ) -> None:
        self._catalog = catalog
        self._source = source
        self._resolver = resolver
        self._lines = lines
        self._calories = calories

    def execute(self, reference: str) -> RecipeNutrition:
        requirements = read_external_requirements(
            self._catalog, self._source, self._resolver, self._lines, reference
        )
        ingredient_ids = list_tagged_ingredient_ids(requirements)
        kcal_per_100g = self._calories.find_kcal_per_100g(ingredient_ids)
        return summarize_nutrition(requirements, kcal_per_100g, None)
