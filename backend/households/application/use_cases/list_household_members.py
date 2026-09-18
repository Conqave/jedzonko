from households.application.access import HouseholdAccessPolicy
from households.application.ports.household_repository import HouseholdRepository
from households.domain.models import HouseholdMember


class ListHouseholdMembers:
    def __init__(self, repository: HouseholdRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, household_id: int) -> list[HouseholdMember]:
        self._access.require_membership(user_id, household_id)
        return self._repository.list_members(household_id)
