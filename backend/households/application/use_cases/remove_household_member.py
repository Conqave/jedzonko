from households.application.access import HouseholdAccessPolicy
from households.application.errors import LastMemberCannotLeaveError
from households.application.ports.household_repository import HouseholdRepository


class RemoveHouseholdMember:
    def __init__(self, repository: HouseholdRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, household_id: int, member_user_id: int) -> None:
        self._access.require_membership(user_id, household_id)
        if self._repository.count_members(household_id) == 1:
            raise LastMemberCannotLeaveError
        self._repository.remove_member(household_id, member_user_id)
