from inventory.composition import build_get_household_inventory
from shopping.application.ports.household_inventory_reader import HouseholdInventoryReader
from shopping.domain.inventory_stock_level import InventoryStockLevel


class InventoryStockGateway(HouseholdInventoryReader):
    def read_stock_levels(self, user_id: int, household_id: int) -> list[InventoryStockLevel]:
        snapshots = build_get_household_inventory().execute(user_id, household_id)
        return [
            InventoryStockLevel(
                product_id=snapshot.product_id,
                product_name=snapshot.product_name,
                quantity=snapshot.quantity,
                minimum_quantity=snapshot.minimum_quantity,
                unit=snapshot.unit,
            )
            for snapshot in snapshots
        ]
