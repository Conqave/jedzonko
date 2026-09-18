from households.application.ports.household_repository import HouseholdRepository
from households.domain.models import HouseholdSummary


class CreateHousehold:
    def __init__(self, repository: HouseholdRepository) -> None:
        self._repository = repository

    def execute(self, name: str, owner_user_id: int) -> HouseholdSummary:
        return self._repository.create_household(name, owner_user_id)
