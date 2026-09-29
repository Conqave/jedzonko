from inventory.application.errors import InventoryCategoryNotFoundError
from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from shared.household_membership import HouseholdMembershipReader, require_membership


class DeleteInventoryCategory:
    def __init__(
        self, repository: InventoryCategoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, category_id: int) -> None:
        household_id = self._repository.find_household_id_for_category(category_id)
        if household_id is None:
            raise InventoryCategoryNotFoundError
        require_membership(self._memberships, user_id, household_id)
        self._repository.delete_category(category_id)
