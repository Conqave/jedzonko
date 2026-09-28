from households.application.ports.household_repository import HouseholdRepository
from households.domain.models import HouseholdMember
from shared.household_membership import HouseholdMembershipReader, require_membership


class ListHouseholdMembers:
    def __init__(
        self, repository: HouseholdRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int) -> list[HouseholdMember]:
        require_membership(self._memberships, user_id, household_id)
        return self._repository.list_members(household_id)
