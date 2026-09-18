from dataclasses import dataclass
from decimal import Decimal

from catalog.domain.measurement import MeasurementUnit


@dataclass(frozen=True, slots=True)
class InventoryStockLevel:
    ingredient_id: int
    ingredient_name: str
    quantity: Decimal
    minimum_quantity: Decimal | None
    unit: MeasurementUnit

    def missing_to_minimum(self) -> Decimal:
        if self.minimum_quantity is None:
            return Decimal("0")
        shortfall = self.minimum_quantity - self.quantity
        return shortfall if shortfall > 0 else Decimal("0")
