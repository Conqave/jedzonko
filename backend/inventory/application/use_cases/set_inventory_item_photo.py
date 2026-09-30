from inventory.application.item_calories import InventoryCalorieCounter
from inventory.application.item_membership import require_item_membership
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemListing
from inventory.domain.photo import InventoryPhoto
from shared.household_membership import HouseholdMembershipReader


class SetInventoryItemPhoto:
    def __init__(
        self,
        repository: InventoryRepository,
        calories: InventoryCalorieCounter,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._calories = calories
        self._memberships = memberships

    def execute(self, user_id: int, item_id: int, photo: InventoryPhoto) -> InventoryItemListing:
        require_item_membership(self._repository, self._memberships, user_id, item_id)
        item = self._repository.set_photo(item_id, photo)
        return self._calories.count(item)
