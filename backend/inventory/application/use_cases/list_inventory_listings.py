from inventory.application.item_calories import InventoryCalorieCounter
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemListing
from shared.household_membership import HouseholdMembershipReader, require_membership


class ListInventoryListings:
    def __init__(
        self,
        repository: InventoryRepository,
        calories: InventoryCalorieCounter,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._calories = calories
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int) -> list[InventoryItemListing]:
        require_membership(self._memberships, user_id, household_id)
        items = self._repository.list_items(household_id)
        return self._calories.count_many(household_id, items)
