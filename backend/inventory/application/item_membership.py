from inventory.application.errors import InventoryItemNotFoundError
from inventory.application.ports.inventory_repository import InventoryRepository
from shared.household_membership import HouseholdMembershipReader, require_membership


def require_item_membership(
    repository: InventoryRepository,
    memberships: HouseholdMembershipReader,
    user_id: int,
    item_id: int,
) -> None:
    household_id = repository.find_household_id_for_item(item_id)
    if household_id is None:
        raise InventoryItemNotFoundError
    require_membership(memberships, user_id, household_id)
