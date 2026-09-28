from inventory.application.use_cases.get_household_inventory import GetHouseholdInventory
from shopping.application.ports.household_inventory_reader import HouseholdInventoryReader
from shopping.domain.inventory_stock_level import InventoryStockLevel


class InventoryStockGateway(HouseholdInventoryReader):
    def __init__(self, get_inventory: GetHouseholdInventory) -> None:
        self._get_inventory = get_inventory

    def get_stock_levels(self, user_id: int, household_id: int) -> list[InventoryStockLevel]:
        return [
            InventoryStockLevel(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                minimum_quantity=item.minimum_quantity,
                unit=item.unit,
            )
            for item in self._get_inventory.execute(user_id, household_id)
        ]
