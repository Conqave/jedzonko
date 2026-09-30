from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ShoppingItemInterpretation:
    ingredient_id: int | None
    ingredient_name: str | None
    quantity: Decimal | None
    unit_code: str | None
