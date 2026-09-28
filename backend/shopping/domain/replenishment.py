from dataclasses import dataclass
from decimal import Decimal

from shopping.domain.inventory_stock_level import InventoryStockLevel
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


@dataclass(frozen=True, slots=True)
class ReplenishmentTarget:
    product_id: int
    amount: Decimal
    unit_code: str
    existing_item_id: int | None


def calculate_replenishment_targets(
    stock_levels: list[InventoryStockLevel], unpurchased_items: list[ShoppingItemSnapshot]
) -> list[ReplenishmentTarget]:
    items_by_product: dict[int, ShoppingItemSnapshot] = {
        item.subject.product_id: item
        for item in unpurchased_items
        if item.subject.product_id is not None and not item.is_purchased
    }
    targets: list[ReplenishmentTarget] = []
    for level in stock_levels:
        shortfall = level.missing_to_minimum()
        if shortfall <= 0:
            continue
        existing = items_by_product.get(level.product_id)
        if existing is None:
            targets.append(
                ReplenishmentTarget(
                    product_id=level.product_id,
                    amount=shortfall,
                    unit_code=level.unit.code,
                    existing_item_id=None,
                )
            )
            continue
        covers_shortfall = (
            existing.unit is not None
            and existing.unit.code == level.unit.code
            and existing.quantity >= shortfall
        )
        if covers_shortfall:
            continue
        targets.append(
            ReplenishmentTarget(
                product_id=level.product_id,
                amount=shortfall,
                unit_code=level.unit.code,
                existing_item_id=existing.id,
            )
        )
    return targets
