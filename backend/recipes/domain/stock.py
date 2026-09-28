from dataclasses import dataclass

from shared.measurement import Quantity


@dataclass(frozen=True, slots=True)
class StockedProduct:

    product_id: int
    product_name: str
    ingredient_id: int | None
    ingredient_name: str | None
    quantity: Quantity
    package_content: Quantity | None
