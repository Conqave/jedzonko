from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShoppingPurchase:
    item_id: int
    chosen_product_id: int | None
