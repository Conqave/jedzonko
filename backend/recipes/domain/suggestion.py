from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MissingRecipeItem:
    ingredient_id: int
    ingredient_name: str
    amount: Decimal
    unit_code: str


@dataclass(frozen=True, slots=True)
class RecipeSuggestion:
    recipe_id: int
    recipe_name: str
    available_item_count: int
    missing_item_count: int
    missing_items: tuple[MissingRecipeItem, ...]
