from catalog.application.use_cases.get_ingredients import GetIngredients
from recipes.application.ports.ingredient_names import IngredientNames


class CatalogIngredientNames(IngredientNames):
    def __init__(self, get_ingredients: GetIngredients) -> None:
        self._get_ingredients = get_ingredients

    def find_names(self, ingredient_ids: set[int]) -> dict[int, str]:
        ingredients = self._get_ingredients.execute(ingredient_ids)
        return {ingredient_id: ingredient.name for ingredient_id, ingredient in ingredients.items()}
