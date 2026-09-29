from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import (
    InvalidShoppingItemError,
    ShoppingItemMergeConflictError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.application.shopping_list_rules import require_known_subject
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_subject import ShoppingSubject


class ChooseShoppingItemProduct:
    def __init__(
        self,
        repository: ShoppingListRepository,
        catalog: CatalogDirectory,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._catalog = catalog
        self._memberships = memberships
        self._transactions = transactions

    def execute(self, user_id: int, item_id: int, product_id: int) -> ShoppingItemSnapshot:
        item = self._repository.find_item(item_id)
        if item is None or item.is_purchased:
            raise ShoppingListItemNotFoundError
        shopping_list = self._repository.find_list(item.list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        if item.subject.ingredient_id is None or item.unit is None:
            raise InvalidShoppingItemError
        product = ShoppingSubject(product_id=product_id)
        require_known_subject(self._catalog, shopping_list.household_id, product)
        with self._transactions.atomic():
            existing = self._repository.find_pending_item(item.list_id, product)
            if existing is None:
                return self._repository.set_item_product(item_id, product_id)
            if existing.unit != item.unit:
                raise ShoppingItemMergeConflictError
            merged_quantity = existing.quantity + item.quantity
            self._repository.delete_item(item_id)
            return self._repository.set_item_quantity(existing.id, merged_quantity, item.unit.code)
