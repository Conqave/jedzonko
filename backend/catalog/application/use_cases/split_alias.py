from catalog.application.errors import IngredientNotFoundError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import Ingredient
from catalog.domain.names import CatalogName
from shared.transactions import TransactionManager


class SplitAlias:
    def __init__(self, ingredients: IngredientRepository, transactions: TransactionManager) -> None:
        self._ingredients = ingredients
        self._transactions = transactions

    def execute(self, alias: str) -> Ingredient:
        name = CatalogName.parse(alias)
        with self._transactions.atomic():
            ingredient = self._ingredients.split_alias(name.normalized_name)
            if ingredient is None:
                raise IngredientNotFoundError
            return ingredient
