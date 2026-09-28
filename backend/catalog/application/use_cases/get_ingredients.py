from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import Ingredient


class GetIngredients:

    def __init__(self, ingredients: IngredientRepository) -> None:
        self._ingredients = ingredients

    def execute(self, ingredient_ids: set[int]) -> dict[int, Ingredient]:
        return self._ingredients.find_many(ingredient_ids)
