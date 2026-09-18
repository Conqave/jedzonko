from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MissingRecipeItem:
    ingredient_id: int
    ingredient_name: str
    amount: Decimal
    unit_code: str
