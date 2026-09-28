from datetime import datetime

from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from shared.household_membership import NotAHouseholdMemberError


class DeleteHousehold:
    def __init__(self, repository: HouseholdLifecycleRepository) -> None:
        self._repository = repository

    def execute(self, user_id: int, household_id: int, now: datetime) -> None:
        if not self._repository.is_member_including_deleted(user_id, household_id):
            raise NotAHouseholdMemberError
        self._repository.mark_deleted(household_id, now)
