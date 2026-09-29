from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LineMeaning:
    ingredient_id: int | None
    quantity: Decimal | None
    unit_code: str | None
