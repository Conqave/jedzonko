from decimal import Decimal

from households.application.access import HouseholdAccessPolicy
from shopping.application.errors import InvalidShoppingItemError, ShoppingListNotFoundError
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


class AddShoppingListItem:
    def __init__(self, repository: ShoppingListRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(
        self,
        user_id: int,
        list_id: int,
        ingredient_id: int | None,
        free_text: str | None,
        quantity: Decimal,
        unit_code: str | None,
    ) -> ShoppingItemSnapshot:
        if (ingredient_id is None) == (free_text is None):
            raise InvalidShoppingItemError
        if ingredient_id is not None and unit_code is None:
            raise InvalidShoppingItemError
        household_id = self._repository.find_household_id_for_list(list_id)
        if household_id is None:
            raise ShoppingListNotFoundError
        self._access.require_membership(user_id, household_id)
        if ingredient_id is None:
            return self._repository.add_item(list_id, None, free_text, quantity, unit_code)
        existing = self._repository.find_pending_item_by_ingredient(list_id, ingredient_id)
        if existing is None:
            return self._repository.add_item(list_id, ingredient_id, None, quantity, unit_code)
        if existing.unit is None or existing.unit.code != unit_code:
            raise InvalidShoppingItemError
        return self._repository.set_item_quantity(
            existing.id, existing.quantity + quantity, unit_code
        )
