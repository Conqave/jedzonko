from dataclasses import dataclass
from datetime import datetime

from households.domain.retention import HOUSEHOLD_RETENTION_PERIOD


@dataclass(frozen=True, slots=True)
class DeletedHousehold:
    id: int
    name: str
    member_count: int
    deleted_at: datetime

    @property
    def purge_after(self) -> datetime:
        return self.deleted_at + HOUSEHOLD_RETENTION_PERIOD
