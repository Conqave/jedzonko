from abc import ABC, abstractmethod
from datetime import datetime

from households.domain.deleted_household import DeletedHousehold
from households.domain.models import HouseholdSummary


class HouseholdLifecycleRepository(ABC):
    @abstractmethod
    def is_member(self, user_id: int, household_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def mark_deleted(self, household_id: int, deleted_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_deleted(self, household_id: int) -> DeletedHousehold | None:
        raise NotImplementedError

    @abstractmethod
    def find_deleted_for_user(self, user_id: int) -> list[DeletedHousehold]:
        raise NotImplementedError

    @abstractmethod
    def restore(self, household_id: int) -> HouseholdSummary:
        raise NotImplementedError

    @abstractmethod
    def find_deleted_before(self, cutoff: datetime) -> list[DeletedHousehold]:
        raise NotImplementedError

    @abstractmethod
    def purge(self, household_ids: list[int]) -> None:
        raise NotImplementedError
