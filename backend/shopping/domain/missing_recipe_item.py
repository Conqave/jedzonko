from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MissingRecipeItem:
    name: str
    normalized_name: str
    amount: Decimal
    unit_code: str
