from inventory.composition import build_get_household_inventory
from inventory.domain.models import InventoryItemSnapshot
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader


class InventoryHouseholdInventoryReader(HouseholdInventoryReader):
    def read_inventory(self, user_id: int, household_id: int) -> list[InventoryItemSnapshot]:
        return build_get_household_inventory().execute(user_id, household_id)
