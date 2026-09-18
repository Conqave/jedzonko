from dataclasses import dataclass
from decimal import Decimal

from catalog.domain.measurement import MeasurementUnit


@dataclass(frozen=True, slots=True)
class ShoppingItemSnapshot:
    id: int
    ingredient_id: int | None
    ingredient_name: str | None
    free_text: str | None
    quantity: Decimal
    unit: MeasurementUnit | None
    is_purchased: bool
