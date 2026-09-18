from decimal import Decimal

from recipes.domain.missing_items import calculate_missing_items, scale_requirements
from recipes.tests.factories import GRAM, KILOGRAM, MILLILITRE, make_requirement, make_snapshot


def test_absent_ingredient_is_fully_missing() -> None:
    requirements = [make_requirement(1, "flour", "500", GRAM)]

    missing = calculate_missing_items(requirements, [])

    assert len(missing) == 1
    assert missing[0].ingredient_id == 1
    assert missing[0].amount == Decimal("500")
    assert missing[0].unit_code == "g"


def test_sufficient_stock_leaves_nothing_missing() -> None:
    requirements = [make_requirement(1, "flour", "500", GRAM)]
    inventory = [make_snapshot(1, "flour", "1", KILOGRAM)]

    assert calculate_missing_items(requirements, inventory) == []


def test_partial_stock_reports_remainder_in_requirement_unit() -> None:
    requirements = [make_requirement(1, "flour", "500", GRAM)]
    inventory = [make_snapshot(1, "flour", "0.2", KILOGRAM)]

    missing = calculate_missing_items(requirements, inventory)

    assert missing[0].amount == Decimal("300")
    assert missing[0].unit_code == "g"


def test_incompatible_units_mark_ingredient_fully_missing() -> None:
    requirements = [make_requirement(1, "milk", "250", MILLILITRE)]
    inventory = [make_snapshot(1, "milk", "900", GRAM)]

    missing = calculate_missing_items(requirements, inventory)

    assert missing[0].amount == Decimal("250")
    assert missing[0].unit_code == "ml"


def test_scaling_multiplies_amounts_by_serving_ratio() -> None:
    requirements = [make_requirement(1, "flour", "500", GRAM)]

    scaled = scale_requirements(requirements, 2, 5)

    assert scaled[0].quantity.amount == Decimal("1250")


def test_scaling_down_reduces_amounts() -> None:
    requirements = [make_requirement(1, "flour", "500", GRAM)]

    scaled = scale_requirements(requirements, 4, 2)

    assert scaled[0].quantity.amount == Decimal("250")
