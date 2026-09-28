from decimal import Decimal

from inventory.application.use_cases.add_quantity_to_inventory import AddQuantityToInventory
from shared.measurement import MeasurementUnit
from shopping.application.ports.inventory_writer import InventoryWriter


class InventoryWriterGateway(InventoryWriter):
    def __init__(self, add_quantity: AddQuantityToInventory) -> None:
        self._add_quantity = add_quantity

    def add_purchased_quantity(
        self, household_id: int, product_id: int, amount: Decimal, unit: MeasurementUnit
    ) -> None:
        self._add_quantity.execute(household_id, product_id, amount, unit)
