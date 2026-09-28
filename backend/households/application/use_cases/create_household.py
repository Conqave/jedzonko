from households.application.ports.household_provisioner import HouseholdProvisioner
from households.application.ports.household_repository import HouseholdRepository
from households.domain.models import HouseholdSummary
from shared.transactions import TransactionManager


class CreateHousehold:
    def __init__(
        self,
        repository: HouseholdRepository,
        provisioner: HouseholdProvisioner,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._provisioner = provisioner
        self._transactions = transactions

    def execute(self, name: str, owner_user_id: int) -> HouseholdSummary:
        with self._transactions.atomic():
            household = self._repository.create_household(name, owner_user_id)
            self._provisioner.provision(household.id)
            return household
