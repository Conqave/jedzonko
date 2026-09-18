from households.application.errors import NotAHouseholdMemberError
from households.application.ports.household_repository import HouseholdRepository


class HouseholdAccessPolicy:
    def __init__(self, repository: HouseholdRepository) -> None:
        self._repository = repository

    def require_membership(self, user_id: int, household_id: int) -> None:
        if not self._repository.is_member(user_id, household_id):
            raise NotAHouseholdMemberError
