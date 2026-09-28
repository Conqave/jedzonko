from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MissingRecipeItem:
    name: str
    ingredient_id: int | None
    stocked_product_id: int | None
    amount: Decimal
    unit_code: str


@dataclass(frozen=True, slots=True)
class RecipeShortfall:
    missing_items: tuple[MissingRecipeItem, ...]
    unmeasured_ingredient_names: tuple[str, ...]
    required_item_count: int
    available_item_count: int

    @property
    def is_ready(self) -> bool:
        return (
            self.required_item_count > 0
            and not self.missing_items
            and not self.unmeasured_ingredient_names
        )


@dataclass(frozen=True, slots=True)
class RecipeSuggestion:
    recipe_id: int
    recipe_name: str
    shortfall: RecipeShortfall
