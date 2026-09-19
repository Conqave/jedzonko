from decimal import Decimal

from recipes.domain.missing_items import calculate_shortfall, scale_requirements
from recipes.tests.factories import GRAM, KILOGRAM, MILLILITRE, make_requirement, make_snapshot


def test_absent_ingredient_is_fully_missing() -> None:
    shortfall = calculate_shortfall([make_requirement("flour", "500", GRAM)], [])

    assert len(shortfall.missing_items) == 1
    assert shortfall.missing_items[0].name == "flour"
    assert shortfall.missing_items[0].amount == Decimal("500")
    assert shortfall.missing_items[0].unit_code == "g"
    assert shortfall.is_ready is False


def test_sufficient_stock_leaves_nothing_missing() -> None:
    requirements = [make_requirement("flour", "500", GRAM)]
    inventory = [make_snapshot(1, "flour", "1", KILOGRAM)]

    shortfall = calculate_shortfall(requirements, inventory)

    assert shortfall.missing_items == ()
    assert shortfall.unmeasured_ingredient_names == ()
    assert shortfall.available_item_count == 1
    assert shortfall.is_ready is True


def test_every_ingredient_in_stock_makes_the_recipe_ready() -> None:
    requirements = [
        make_requirement("flour", "500", GRAM),
        make_requirement("milk", "250", MILLILITRE),
    ]
    inventory = [
        make_snapshot(1, "flour", "1", KILOGRAM),
        make_snapshot(2, "milk", "900", MILLILITRE),
    ]

    assert calculate_shortfall(requirements, inventory).is_ready is True


def test_one_short_ingredient_makes_the_recipe_not_ready() -> None:
    requirements = [
        make_requirement("flour", "500", GRAM),
        make_requirement("milk", "250", MILLILITRE),
    ]
    inventory = [
        make_snapshot(1, "flour", "1", KILOGRAM),
        make_snapshot(2, "milk", "100", MILLILITRE),
    ]

    shortfall = calculate_shortfall(requirements, inventory)

    assert [item.name for item in shortfall.missing_items] == ["milk"]
    assert shortfall.is_ready is False


def test_recipe_without_ingredients_is_not_ready() -> None:
    assert calculate_shortfall([], []).is_ready is False


def test_partial_stock_reports_remainder_in_requirement_unit() -> None:
    requirements = [make_requirement("flour", "500", GRAM)]
    inventory = [make_snapshot(1, "flour", "0.2", KILOGRAM)]

    shortfall = calculate_shortfall(requirements, inventory)

    assert shortfall.missing_items[0].amount == Decimal("300")
    assert shortfall.missing_items[0].unit_code == "g"


def test_incomparable_quantity_is_reported_and_blocks_readiness() -> None:
    requirements = [make_requirement("milk", "250", MILLILITRE)]
    inventory = [make_snapshot(1, "milk", "900", GRAM)]

    shortfall = calculate_shortfall(requirements, inventory)

    assert shortfall.unmeasured_ingredient_names == ("milk",)
    assert shortfall.missing_items[0].amount == Decimal("250")
    assert shortfall.missing_items[0].unit_code == "ml"
    assert shortfall.is_ready is False


def test_scaling_multiplies_amounts_by_serving_ratio() -> None:
    scaled = scale_requirements([make_requirement("flour", "500", GRAM)], 2, 5)

    assert scaled[0].quantity.amount == Decimal("1250")


def test_scaling_down_reduces_amounts() -> None:
    scaled = scale_requirements([make_requirement("flour", "500", GRAM)], 4, 2)

    assert scaled[0].quantity.amount == Decimal("250")
