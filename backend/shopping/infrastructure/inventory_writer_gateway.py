from decimal import Decimal

from catalog.domain.measurement import MeasurementUnit
from inventory.composition import build_add_quantity_to_inventory
from shopping.application.ports.inventory_writer import InventoryWriter


class InventoryWriterGateway(InventoryWriter):
    def add_purchased_quantity(
        self, household_id: int, ingredient_id: int, amount: Decimal, unit: MeasurementUnit
    ) -> None:
        build_add_quantity_to_inventory().execute(household_id, ingredient_id, amount, unit)
