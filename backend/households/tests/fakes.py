from dataclasses import dataclass
from datetime import datetime

from households.application.errors import HouseholdNotFoundError
from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from households.domain.deleted_household import DeletedHousehold
from households.domain.models import HouseholdSummary


@dataclass
class FakeHouseholdRow:
    id: int
    name: str
    member_ids: set[int]
    deleted_at: datetime | None


class FakeHouseholdLifecycleRepository(HouseholdLifecycleRepository):
    def __init__(self, rows: list[FakeHouseholdRow]) -> None:
        self.rows = rows
        self.purged: list[int] = []

    def is_member(self, user_id: int, household_id: int) -> bool:
        row = self._find(household_id)
        return row is not None and user_id in row.member_ids

    def mark_deleted(self, household_id: int, deleted_at: datetime) -> None:
        row = self._find(household_id)
        if row is None or row.deleted_at is not None:
            raise HouseholdNotFoundError
        row.deleted_at = deleted_at

    def find_deleted(self, household_id: int) -> DeletedHousehold | None:
        row = self._find(household_id)
        if row is None or row.deleted_at is None:
            return None
        return _to_deleted(row)

    def find_deleted_for_user(self, user_id: int) -> list[DeletedHousehold]:
        return [
            _to_deleted(row)
            for row in self.rows
            if row.deleted_at is not None and user_id in row.member_ids
        ]

    def restore(self, household_id: int) -> HouseholdSummary:
        row = self._find(household_id)
        if row is None or row.deleted_at is None:
            raise HouseholdNotFoundError
        row.deleted_at = None
        return HouseholdSummary(id=row.id, name=row.name, member_count=len(row.member_ids))

    def find_deleted_before(self, cutoff: datetime) -> list[DeletedHousehold]:
        return [
            _to_deleted(row)
            for row in self.rows
            if row.deleted_at is not None and row.deleted_at <= cutoff
        ]

    def purge(self, household_ids: list[int]) -> None:
        self.purged.extend(household_ids)
        self.rows = [row for row in self.rows if row.id not in household_ids]

    def _find(self, household_id: int) -> FakeHouseholdRow | None:
        for row in self.rows:
            if row.id == household_id:
                return row
        return None


def _to_deleted(row: FakeHouseholdRow) -> DeletedHousehold:
    if row.deleted_at is None:
        raise HouseholdNotFoundError
    return DeletedHousehold(
        id=row.id,
        name=row.name,
        member_count=len(row.member_ids),
        deleted_at=row.deleted_at,
    )
