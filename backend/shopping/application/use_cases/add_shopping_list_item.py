from decimal import Decimal

from households.application.access import HouseholdAccessPolicy
from shopping.application.errors import (
    InvalidShoppingItemError,
    ProductNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.ports.product_resolver import ProductResolver
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


class AddShoppingListItem:
    def __init__(
        self,
        repository: ShoppingListRepository,
        access: HouseholdAccessPolicy,
        products: ProductResolver,
    ) -> None:
        self._repository = repository
        self._access = access
        self._products = products

    def execute(
        self,
        user_id: int,
        list_id: int,
        product_id: int | None,
        free_text: str | None,
        quantity: Decimal,
        unit_code: str | None,
    ) -> ShoppingItemSnapshot:
        if (product_id is None) == (free_text is None):
            raise InvalidShoppingItemError
        if product_id is not None and unit_code is None:
            raise InvalidShoppingItemError
        household_id = self._repository.find_household_id_for_list(list_id)
        if household_id is None:
            raise ShoppingListNotFoundError
        self._access.require_membership(user_id, household_id)
        if product_id is None:
            return self._repository.add_item(list_id, None, free_text, quantity, unit_code)
        if not self._products.is_household_product(household_id, product_id):
            raise ProductNotFoundError
        existing = self._repository.find_pending_item_by_product(list_id, product_id)
        if existing is None:
            return self._repository.add_item(list_id, product_id, None, quantity, unit_code)
        if existing.unit is None or existing.unit.code != unit_code:
            raise InvalidShoppingItemError
        return self._repository.set_item_quantity(
            existing.id, existing.quantity + quantity, unit_code
        )
