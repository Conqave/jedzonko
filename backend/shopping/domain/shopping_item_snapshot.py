from dataclasses import dataclass
from decimal import Decimal

from shared.measurement import MeasurementUnit


@dataclass(frozen=True, slots=True)
class ShoppingItemSnapshot:
    id: int
    product_id: int | None
    product_name: str | None
    free_text: str | None
    quantity: Decimal
    unit: MeasurementUnit | None
    is_purchased: bool
