from decimal import Decimal

from catalog.domain.measurement import MeasurementDimension
from catalog.domain.measurement import MeasurementUnit as UnitValue
from catalog.models import MeasurementUnit
from inventory.composition import build_consume_inventory_quantity
from recipes.application.errors import MeasurementUnitNotFoundError
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer


class InventoryHouseholdInventoryConsumer(HouseholdInventoryConsumer):
    def consume(
        self, household_id: int, ingredient_id: int, amount: Decimal, unit_code: str
    ) -> None:
        unit = MeasurementUnit.objects.filter(code=unit_code).first()
        if unit is None:
            raise MeasurementUnitNotFoundError
        build_consume_inventory_quantity().execute(
            household_id,
            ingredient_id,
            amount,
            UnitValue(
                code=unit.code,
                dimension=MeasurementDimension(unit.dimension),
                factor_to_base=unit.factor_to_base,
            ),
        )
