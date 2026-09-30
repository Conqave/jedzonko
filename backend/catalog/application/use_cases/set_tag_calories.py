from dataclasses import replace
from decimal import Decimal

from catalog.application.errors import IngredientNotFoundError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.calories import TagCalories
from catalog.domain.ingredient import Ingredient
from shared.transactions import TransactionManager


class SetTagCalories:
    def __init__(self, ingredients: IngredientRepository, transactions: TransactionManager) -> None:
        self._ingredients = ingredients
        self._transactions = transactions

    def execute(self, ingredient_id: int, kcal_per_100g: Decimal | None) -> Ingredient:
        calories = None if kcal_per_100g is None else TagCalories.manual(kcal_per_100g)
        with self._transactions.atomic():
            ingredient = self._ingredients.find(ingredient_id)
            if ingredient is None:
                raise IngredientNotFoundError
            self._ingredients.save_calories(ingredient_id, calories)
        return replace(ingredient, calories=calories)
