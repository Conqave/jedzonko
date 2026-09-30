from datetime import datetime

from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingListItemNotFoundError
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.application.use_cases.buy_shopping_item import BuyShoppingItem
from shopping.domain.shopping_purchase import ShoppingPurchase


class BuyShoppingItems:
    def __init__(
        self,
        repository: ShoppingListRepository,
        buy_item: BuyShoppingItem,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._buy_item = buy_item
        self._transactions = transactions

    def execute(
        self,
        user_id: int,
        list_id: int,
        purchases: tuple[ShoppingPurchase, ...],
        now: datetime,
    ) -> None:
        with self._transactions.atomic():
            for purchase in purchases:
                item = self._repository.find_item(purchase.item_id)
                if item is None or item.list_id != list_id:
                    raise ShoppingListItemNotFoundError
                self._buy_item.execute(user_id, purchase, now)
