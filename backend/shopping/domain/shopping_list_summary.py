from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShoppingListSummary:
    id: int
    household_id: int
    name: str
    is_primary: bool
    item_count: int
