from dataclasses import dataclass
from decimal import Decimal

from shopping.domain.shopping_subject import ShoppingSubject


@dataclass(frozen=True, slots=True)
class MissingRecipeItem:
    name: str
    ingredient_id: int | None
    stocked_product_id: int | None
    amount: Decimal | None
    unit_code: str | None

    def subject(self, only_product_of_ingredient: int | None) -> ShoppingSubject:
        if self.stocked_product_id is not None:
            return ShoppingSubject(product_id=self.stocked_product_id)
        if only_product_of_ingredient is not None:
            return ShoppingSubject(product_id=only_product_of_ingredient)
        if self.ingredient_id is not None:
            return ShoppingSubject(ingredient_id=self.ingredient_id)
        return ShoppingSubject(free_text=self.name)
