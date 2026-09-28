from dataclasses import dataclass

from shopping.domain.errors import InvalidShoppingSubjectError


@dataclass(frozen=True, slots=True)
class ShoppingSubject:

    product_id: int | None = None
    ingredient_id: int | None = None
    free_text: str | None = None

    def __post_init__(self) -> None:
        present = [
            value is not None for value in (self.product_id, self.ingredient_id, self.free_text)
        ]
        if present.count(True) != 1:
            raise InvalidShoppingSubjectError(
                "A shopping item is about exactly one product, ingredient or text."
            )
        if self.free_text is not None and not self.free_text.strip():
            raise InvalidShoppingSubjectError("Free text is empty.")

    @property
    def is_measured(self) -> bool:
        return self.free_text is None
