from decimal import Decimal

from inventory.composition import build_add_quantity_to_inventory
from shared.measurement import MeasurementUnit
from shopping.application.ports.inventory_writer import InventoryWriter


class InventoryWriterGateway(InventoryWriter):
    def add_purchased_quantity(
        self, household_id: int, product_id: int, amount: Decimal, unit: MeasurementUnit
    ) -> None:
        build_add_quantity_to_inventory().execute(household_id, product_id, amount, unit)
