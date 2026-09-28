from catalog.application.errors import DuplicateIngredientNameError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.transaction_manager import TransactionManager
from catalog.domain.ingredient import Ingredient, IngredientNameSource
from catalog.domain.names import IngredientNameText


class CreateIngredient:
    def __init__(self, repository: IngredientRepository, transactions: TransactionManager) -> None:
        self._repository = repository
        self._transactions = transactions

    def execute(self, name: str, source: IngredientNameSource) -> Ingredient:
        text = IngredientNameText.parse(name)
        with self._transactions.atomic():
            if self._repository.find_by_normalized_name(text.normalized_name) is not None:
                raise DuplicateIngredientNameError
            return self._repository.create(text, source)
