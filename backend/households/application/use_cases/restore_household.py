from datetime import datetime

from households.application.errors import (
    HouseholdNotFoundError,
    RecoveryWindowExpiredError,
)
from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from households.domain.models import HouseholdSummary
from shared.household_membership import NotAHouseholdMemberError


class RestoreHousehold:
    def __init__(self, repository: HouseholdLifecycleRepository) -> None:
        self._repository = repository

    def execute(self, user_id: int, household_id: int, now: datetime) -> HouseholdSummary:
        if not self._repository.is_member_including_deleted(user_id, household_id):
            raise NotAHouseholdMemberError
        deleted = self._repository.find_deleted(household_id)
        if deleted is None:
            raise HouseholdNotFoundError
        if now >= deleted.purge_after:
            raise RecoveryWindowExpiredError
        return self._repository.restore(household_id)
