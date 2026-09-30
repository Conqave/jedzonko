from decimal import Decimal

from catalog.application.use_cases.get_ingredients import GetIngredients
from recipes.application.ports.ingredient_calories import IngredientCalories


class CatalogIngredientCalories(IngredientCalories):
    def __init__(self, get_ingredients: GetIngredients) -> None:
        self._get_ingredients = get_ingredients

    def find_kcal_per_100g(self, ingredient_ids: set[int]) -> dict[int, Decimal]:
        ingredients = self._get_ingredients.execute(ingredient_ids)
        return {
            ingredient_id: ingredient.calories.kcal_per_100g
            for ingredient_id, ingredient in ingredients.items()
            if ingredient.calories is not None
        }
