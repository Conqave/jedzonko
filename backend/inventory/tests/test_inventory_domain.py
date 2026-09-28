from decimal import Decimal

import pytest

from inventory.domain.models import InventoryItemSnapshot
from shared.measurement import (
    IncompatibleUnitsError,
    MeasurementDimension,
    MeasurementUnit,
    Quantity,
)

GRAM = MeasurementUnit(code="g", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1"))
KILOGRAM = MeasurementUnit(
    code="kg", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1000")
)
LITRE = MeasurementUnit(
    code="l", dimension=MeasurementDimension.VOLUME, factor_to_base=Decimal("1000")
)


def _snapshot(quantity: str, minimum: str | None) -> InventoryItemSnapshot:
    return InventoryItemSnapshot(
        id=1,
        product_id=1,
        product_name="Mąka",
        normalized_name="maka",
            tag_names=(),
        quantity=Decimal(quantity),
        unit=KILOGRAM,
        package_quantity=None,
        package_unit=None,
        minimum_quantity=None if minimum is None else Decimal(minimum),
        category_id=None,
        category_name=None,
        photo_url=None,
    )


def test_quantity_converts_within_the_same_dimension() -> None:
    converted = Quantity(amount=Decimal("2"), unit=KILOGRAM).convert_to(GRAM)

    assert converted.amount == Decimal("2000")
    assert converted.unit == GRAM


def test_quantity_refuses_cross_dimension_conversion() -> None:
    with pytest.raises(IncompatibleUnitsError):
        Quantity(amount=Decimal("1"), unit=KILOGRAM).convert_to(LITRE)


def test_quantity_subtracts_after_converting_the_other_operand() -> None:
    remaining = Quantity(amount=Decimal("2"), unit=KILOGRAM).subtract(
        Quantity(amount=Decimal("500"), unit=GRAM)
    )

    assert remaining.amount == Decimal("1.5")
    assert remaining.unit == KILOGRAM


def test_item_without_minimum_is_never_below_minimum() -> None:
    assert _snapshot("0", None).is_below_minimum() is False
    assert _snapshot("0", None).missing_to_minimum() == Decimal("0")


def test_item_below_minimum_reports_the_shortfall() -> None:
    item = _snapshot("1", "3")

    assert item.is_below_minimum() is True
    assert item.missing_to_minimum() == Decimal("2")


def test_item_at_minimum_is_not_below_minimum() -> None:
    item = _snapshot("3", "3")

    assert item.is_below_minimum() is False
    assert item.missing_to_minimum() == Decimal("0")
