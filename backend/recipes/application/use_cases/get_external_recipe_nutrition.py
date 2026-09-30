from recipes.application.external_content import read_external_content
from recipes.application.external_requirements import resolve_external_requirements
from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.application.ports.ingredient_nutrition_facts import IngredientNutritionFacts
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.nutrition import (
    RecipeNutrition,
    list_tagged_ingredient_ids,
    summarize_nutrition,
)
from recipes.domain.servings import read_servings


class GetExternalRecipeNutrition:
    def __init__(
        self,
        catalog: ExternalRecipeCatalog,
        source: RecipeSource,
        resolver: IngredientResolver,
        lines: IngredientLines,
        nutrition_facts: IngredientNutritionFacts,
    ) -> None:
        self._catalog = catalog
        self._source = source
        self._resolver = resolver
        self._lines = lines
        self._nutrition_facts = nutrition_facts

    def execute(self, reference: str) -> RecipeNutrition:
        content = read_external_content(self._catalog, self._source, reference)
        requirements = resolve_external_requirements(
            content.ingredients, self._resolver, self._lines
        )
        ingredient_ids = list_tagged_ingredient_ids(requirements)
        facts = self._nutrition_facts.find_nutrition_facts(ingredient_ids)
        servings = read_servings(content.yield_label)
        return summarize_nutrition(requirements, facts, servings)
