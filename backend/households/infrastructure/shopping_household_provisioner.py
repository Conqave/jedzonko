from households.application.ports.household_provisioner import HouseholdProvisioner
from shopping.application.use_cases.create_primary_shopping_list import CreatePrimaryShoppingList


class ShoppingHouseholdProvisioner(HouseholdProvisioner):
    def __init__(self, create_primary_list: CreatePrimaryShoppingList) -> None:
        self._create_primary_list = create_primary_list

    def provision(self, household_id: int) -> None:
        self._create_primary_list.execute(household_id)
