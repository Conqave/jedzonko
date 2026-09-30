from dataclasses import dataclass

from shared.item_calories import ItemCalories
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


@dataclass(frozen=True, slots=True)
class ShoppingItemListing:
    item: ShoppingItemSnapshot
    calories: ItemCalories
