from datetime import datetime

from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from households.domain.deleted_household import DeletedHousehold
from households.domain.retention import HOUSEHOLD_RETENTION_PERIOD


class PurgeExpiredHouseholds:
    def __init__(self, repository: HouseholdLifecycleRepository) -> None:
        self._repository = repository

    def execute(self, now: datetime, dry_run: bool) -> list[DeletedHousehold]:
        expired = self._repository.find_deleted_before(now - HOUSEHOLD_RETENTION_PERIOD)
        if expired and not dry_run:
            self._repository.purge([household.id for household in expired])
        return expired
