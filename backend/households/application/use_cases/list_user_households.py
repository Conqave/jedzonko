from households.application.ports.household_repository import HouseholdRepository
from households.domain.models import HouseholdSummary


class ListUserHouseholds:
    def __init__(self, repository: HouseholdRepository) -> None:
        self._repository = repository

    def execute(self, user_id: int) -> list[HouseholdSummary]:
        return self._repository.find_households_for_user(user_id)
