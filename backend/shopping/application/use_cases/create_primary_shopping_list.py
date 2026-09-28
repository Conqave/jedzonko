from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_list_summary import ShoppingListSummary

PRIMARY_LIST_NAME = "Lista zakupów"


class CreatePrimaryShoppingList:

    def __init__(self, repository: ShoppingListRepository) -> None:
        self._repository = repository

    def execute(self, household_id: int) -> ShoppingListSummary:
        return self._repository.create_list(household_id, PRIMARY_LIST_NAME, is_primary=True)
