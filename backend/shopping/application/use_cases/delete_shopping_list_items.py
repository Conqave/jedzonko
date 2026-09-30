from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingListItemNotFoundError
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.application.use_cases.delete_shopping_list_item import DeleteShoppingListItem


class DeleteShoppingListItems:
    def __init__(
        self,
        repository: ShoppingListRepository,
        delete_item: DeleteShoppingListItem,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._delete_item = delete_item
        self._transactions = transactions

    def execute(self, user_id: int, list_id: int, item_ids: tuple[int, ...]) -> None:
        with self._transactions.atomic():
            for item_id in item_ids:
                item = self._repository.find_item(item_id)
                if item is None or item.list_id != list_id:
                    raise ShoppingListItemNotFoundError
                self._delete_item.execute(user_id, item_id)
