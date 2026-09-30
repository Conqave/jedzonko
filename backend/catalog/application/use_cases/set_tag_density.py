from dataclasses import replace
from decimal import Decimal

from catalog.application.errors import IngredientNotFoundError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.conversions import Density
from catalog.domain.ingredient import Ingredient
from shared.transactions import TransactionManager


class SetTagDensity:
    def __init__(self, ingredients: IngredientRepository, transactions: TransactionManager) -> None:
        self._ingredients = ingredients
        self._transactions = transactions

    def execute(self, ingredient_id: int, grams_per_ml: Decimal | None) -> Ingredient:
        density = None if grams_per_ml is None else Density.manual(grams_per_ml)
        with self._transactions.atomic():
            ingredient = self._ingredients.find(ingredient_id)
            if ingredient is None:
                raise IngredientNotFoundError
            self._ingredients.save_density(ingredient_id, density)
        return replace(ingredient, density=density)
