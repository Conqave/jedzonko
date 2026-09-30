from catalog.application.use_cases.get_ingredients import GetIngredients
from catalog.domain.nutrition_facts import to_nutrition_facts
from recipes.application.ports.ingredient_nutrition_facts import IngredientNutritionFacts
from shared.nutrition import NutritionFacts


class CatalogIngredientNutritionFacts(IngredientNutritionFacts):
    def __init__(self, get_ingredients: GetIngredients) -> None:
        self._get_ingredients = get_ingredients

    def find_nutrition_facts(self, ingredient_ids: set[int]) -> dict[int, NutritionFacts]:
        ingredients = self._get_ingredients.execute(ingredient_ids)
        return {
            ingredient_id: to_nutrition_facts(ingredient)
            for ingredient_id, ingredient in ingredients.items()
        }
