from abc import abstractmethod

from households.application.ports.household_membership_reader import HouseholdMembershipReader
from households.domain.models import HouseholdMember, HouseholdSummary


class HouseholdRepository(HouseholdMembershipReader):
    @abstractmethod
    def find_households_for_user(self, user_id: int) -> list[HouseholdSummary]:
        raise NotImplementedError

    @abstractmethod
    def find_household(self, household_id: int) -> HouseholdSummary | None:
        raise NotImplementedError

    @abstractmethod
    def list_members(self, household_id: int) -> list[HouseholdMember]:
        raise NotImplementedError

    @abstractmethod
    def create_household(self, name: str, owner_user_id: int) -> HouseholdSummary:
        raise NotImplementedError

    @abstractmethod
    def rename_household(self, household_id: int, name: str) -> HouseholdSummary:
        raise NotImplementedError

    @abstractmethod
    def add_member(self, household_id: int, username: str) -> HouseholdMember:
        raise NotImplementedError

    @abstractmethod
    def remove_member(self, household_id: int, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def count_members(self, household_id: int) -> int:
        raise NotImplementedError
