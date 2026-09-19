from dataclasses import dataclass
from decimal import Decimal

from shared.measurement import MeasurementUnit, Quantity


@dataclass(frozen=True, slots=True)
class InventoryItemSnapshot:
    id: int
    product_id: int
    product_name: str
    normalized_name: str
    quantity: Decimal
    unit: MeasurementUnit
    minimum_quantity: Decimal | None
    category_name: str | None
    photo_url: str | None

    def as_quantity(self) -> Quantity:
        return Quantity(amount=self.quantity, unit=self.unit)

    def is_below_minimum(self) -> bool:
        if self.minimum_quantity is None:
            return False
        return self.quantity < self.minimum_quantity

    def missing_to_minimum(self) -> Decimal:
        if self.minimum_quantity is None:
            return Decimal("0")
        shortfall = self.minimum_quantity - self.quantity
        return shortfall if shortfall > 0 else Decimal("0")
