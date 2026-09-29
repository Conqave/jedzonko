from dataclasses import dataclass

from shared.measurement import Quantity


@dataclass(frozen=True, slots=True)
class StockedProduct:

    product_id: int
    product_name: str
    ingredient_ids: frozenset[int]
    tag_names: tuple[str, ...]
    quantity: Quantity
    package_content: Quantity | None
