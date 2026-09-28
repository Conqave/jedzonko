from abc import ABC, abstractmethod


class NotAHouseholdMemberError(Exception):
    pass


class HouseholdMembershipReader(ABC):

    @abstractmethod
    def is_member(self, user_id: int, household_id: int) -> bool:
        raise NotImplementedError


def require_membership(
    memberships: HouseholdMembershipReader, user_id: int, household_id: int
) -> None:
    if not memberships.is_member(user_id, household_id):
        raise NotAHouseholdMemberError
