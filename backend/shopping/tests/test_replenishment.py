from decimal import Decimal

from shared.measurement import MeasurementDimension, MeasurementUnit
from shopping.domain.inventory_stock_level import InventoryStockLevel
from shopping.domain.replenishment import calculate_replenishment_targets
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_item_status import ShoppingItemStatus
from shopping.domain.shopping_subject import ShoppingSubject

GRAM = MeasurementUnit(code="g", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1"))
KILOGRAM = MeasurementUnit(
    code="kg", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1000")
)


def _level(quantity: str, minimum: str | None) -> InventoryStockLevel:
    return InventoryStockLevel(
        product_id=1,
        product_name="Mąka",
        quantity=Decimal(quantity),
        minimum_quantity=None if minimum is None else Decimal(minimum),
        unit=GRAM,
    )


def _item(item_id: int, quantity: str, unit: MeasurementUnit | None) -> ShoppingItemSnapshot:
    return ShoppingItemSnapshot(
        id=item_id,
        list_id=1,
        subject=ShoppingSubject(product_id=1),
        name="Mąka",
        quantity=Decimal(quantity),
        unit=unit,
        status=ShoppingItemStatus.PENDING,
        purchased_at=None,
    )


def test_no_target_when_stock_is_above_minimum() -> None:
    assert calculate_replenishment_targets([_level("500", "300")], []) == []


def test_no_target_without_minimum_quantity() -> None:
    assert calculate_replenishment_targets([_level("10", None)], []) == []


def test_creates_target_for_shortfall() -> None:
    targets = calculate_replenishment_targets([_level("100", "300")], [])
    assert len(targets) == 1
    assert targets[0].amount == Decimal("200")
    assert targets[0].unit_code == "g"
    assert targets[0].existing_item_id is None


def test_existing_item_covering_shortfall_produces_no_target() -> None:
    targets = calculate_replenishment_targets([_level("100", "300")], [_item(7, "200", GRAM)])
    assert targets == []


def test_existing_item_below_shortfall_is_raised_not_duplicated() -> None:
    targets = calculate_replenishment_targets([_level("100", "300")], [_item(7, "50", GRAM)])
    assert len(targets) == 1
    assert targets[0].existing_item_id == 7
    assert targets[0].amount == Decimal("200")


def test_existing_item_with_other_unit_is_rewritten() -> None:
    targets = calculate_replenishment_targets([_level("100", "300")], [_item(7, "5", KILOGRAM)])
    assert len(targets) == 1
    assert targets[0].existing_item_id == 7
    assert targets[0].unit_code == "g"


def test_free_text_items_are_ignored() -> None:
    free_text_item = ShoppingItemSnapshot(
        id=9,
        list_id=1,
        subject=ShoppingSubject(free_text="Ręczniki"),
        name="Ręczniki",
        quantity=Decimal("1"),
        unit=None,
        status=ShoppingItemStatus.PENDING,
        purchased_at=None,
    )
    targets = calculate_replenishment_targets([_level("100", "300")], [free_text_item])
    assert len(targets) == 1
    assert targets[0].existing_item_id is None
