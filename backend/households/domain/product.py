from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductSummary:
    id: int
    household_id: int
    name: str
    normalized_name: str
    default_unit_code: str
    is_food: bool
