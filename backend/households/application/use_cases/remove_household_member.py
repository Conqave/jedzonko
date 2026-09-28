from households.application.errors import LastMemberCannotLeaveError
from households.application.ports.household_repository import HouseholdRepository
from shared.household_membership import HouseholdMembershipReader, require_membership


class RemoveHouseholdMember:
    def __init__(
        self, repository: HouseholdRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int, member_user_id: int) -> None:
        require_membership(self._memberships, user_id, household_id)
        if self._repository.count_members(household_id) == 1:
            raise LastMemberCannotLeaveError
        self._repository.remove_member(household_id, member_user_id)
