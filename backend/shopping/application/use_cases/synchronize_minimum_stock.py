from django.db import transaction

from households.application.access import HouseholdAccessPolicy
from shopping.application.errors import ShoppingListNotFoundError
from shopping.application.ports.household_inventory_reader import HouseholdInventoryReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.replenishment import calculate_replenishment_targets
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


class SynchronizeMinimumStock:
    def __init__(
        self,
        repository: ShoppingListRepository,
        access: HouseholdAccessPolicy,
        inventory: HouseholdInventoryReader,
    ) -> None:
        self._repository = repository
        self._access = access
        self._inventory = inventory

    def execute(self, user_id: int, list_id: int) -> list[ShoppingItemSnapshot]:
        household_id = self._repository.find_household_id_for_list(list_id)
        if household_id is None:
            raise ShoppingListNotFoundError
        self._access.require_membership(user_id, household_id)
        with transaction.atomic():
            primary_list = self._repository.get_or_create_primary_list(household_id)
        stock_levels = self._inventory.read_stock_levels(user_id, household_id)
        pending = self._repository.list_pending_items(primary_list.id)
        targets = calculate_replenishment_targets(stock_levels, pending)
        for target in targets:
            if target.existing_item_id is None:
                self._repository.add_item(
                    primary_list.id, target.ingredient_id, None, target.amount, target.unit_code
                )
                continue
            self._repository.set_item_quantity(
                target.existing_item_id, target.amount, target.unit_code
            )
        return self._repository.list_items(primary_list.id)
