from decimal import Decimal

from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import PrimaryShoppingListNotFoundError
from shopping.application.item_calories import ShoppingCalorieCounter
from shopping.application.ports.household_inventory_reader import HouseholdInventoryReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.replenishment import calculate_replenishment_targets
from shopping.domain.shopping_item_listing import ShoppingItemListing
from shopping.domain.shopping_subject import ShoppingSubject


class SynchronizeMinimumStock:

    def __init__(
        self,
        repository: ShoppingListRepository,
        inventory: HouseholdInventoryReader,
        calories: ShoppingCalorieCounter,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._inventory = inventory
        self._calories = calories
        self._memberships = memberships
        self._transactions = transactions

    def execute(self, user_id: int, household_id: int) -> list[ShoppingItemListing]:
        require_membership(self._memberships, user_id, household_id)
        primary = self._repository.find_primary_list(household_id)
        if primary is None:
            raise PrimaryShoppingListNotFoundError
        stock_levels = self._inventory.get_stock_levels(user_id, household_id)
        with self._transactions.atomic():
            pending = self._repository.list_pending_items(primary.id)
            for target in calculate_replenishment_targets(stock_levels, pending):
                amount = Decimal(target.amount)
                if target.existing_item_id is None:
                    self._repository.add_item(
                        primary.id,
                        ShoppingSubject(product_id=target.product_id),
                        amount,
                        target.unit_code,
                    )
                    continue
                self._repository.set_item_quantity(
                    target.existing_item_id, amount, target.unit_code
                )
        items = self._repository.list_items(primary.id)
        return self._calories.count_many(household_id, items)
