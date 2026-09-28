from catalog.application.errors import DuplicateIngredientNameError, IngredientNotFoundError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import IngredientName, IngredientNameKind, IngredientNameSource
from catalog.domain.names import CatalogName
from shared.transactions import TransactionManager


class AddIngredientAlias:
    def __init__(self, repository: IngredientRepository, transactions: TransactionManager) -> None:
        self._repository = repository
        self._transactions = transactions

    def execute(
        self, ingredient_id: int, name: str, source: IngredientNameSource
    ) -> IngredientName:
        text = CatalogName.parse(name)
        with self._transactions.atomic():
            if self._repository.find(ingredient_id) is None:
                raise IngredientNotFoundError
            if self._repository.find_by_normalized_name(text.normalized_name) is not None:
                raise DuplicateIngredientNameError
            return self._repository.add_name(ingredient_id, text, IngredientNameKind.ALIAS, source)
