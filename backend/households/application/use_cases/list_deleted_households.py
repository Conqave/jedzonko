from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from households.domain.deleted_household import DeletedHousehold


class ListDeletedHouseholds:
    def __init__(self, repository: HouseholdLifecycleRepository) -> None:
        self._repository = repository

    def execute(self, user_id: int) -> list[DeletedHousehold]:
        return self._repository.find_deleted_for_user(user_id)
