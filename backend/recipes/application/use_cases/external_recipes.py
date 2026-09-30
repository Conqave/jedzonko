from dataclasses import dataclass

from recipes.application.use_cases.calculate_external_recipe_shortfall import (
    CalculateExternalRecipeShortfall,
)
from recipes.application.use_cases.get_external_recipe import GetExternalRecipe
from recipes.application.use_cases.get_external_recipe_nutrition import (
    GetExternalRecipeNutrition,
)
from recipes.application.use_cases.search_external_recipes import SearchExternalRecipes
from recipes.application.use_cases.suggest_external_recipes_from_inventory import (
    SuggestExternalRecipesFromInventory,
)


@dataclass(frozen=True, slots=True)
class ExternalRecipes:
    search: SearchExternalRecipes
    suggest_from_inventory: SuggestExternalRecipesFromInventory
    get: GetExternalRecipe
    calculate_shortfall: CalculateExternalRecipeShortfall
    get_nutrition: GetExternalRecipeNutrition
