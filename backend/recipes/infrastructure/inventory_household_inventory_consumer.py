from decimal import Decimal

from inventory.composition import build_consume_inventory_quantity
from recipes.application.errors import MeasurementUnitNotFoundError
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from shared.measurement_units import find_measurement_unit


class InventoryHouseholdInventoryConsumer(HouseholdInventoryConsumer):
    def consume(self, household_id: int, product_id: int, amount: Decimal, unit_code: str) -> None:
        unit = find_measurement_unit(unit_code)
        if unit is None:
            raise MeasurementUnitNotFoundError
        build_consume_inventory_quantity().execute(household_id, product_id, amount, unit)
