from abc import ABC, abstractmethod


class HouseholdMembershipReader(ABC):
    @abstractmethod
    def is_member(self, user_id: int, household_id: int) -> bool:
        raise NotImplementedError
