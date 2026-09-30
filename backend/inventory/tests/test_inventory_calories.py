from decimal import Decimal

from inventory.application.item_calories import InventoryCalorieCounter
from inventory.domain.models import InventoryItemSnapshot
from inventory.tests.fakes import FakeProductNutritionReader
from shared.item_calories import SubjectNutrition, TagGap
from shared.measurement_units import find_measurement_unit
from shared.nutrition import NutritionFacts, UncountedReason

HOME = 10
FLOUR = 1
SALT = 2
EGGS = 3
FLOUR_FACTS = NutritionFacts(kcal_per_100g=Decimal("364"), grams_per_piece=None, grams_per_ml=None)
EGG_FACTS = NutritionFacts(kcal_per_100g=Decimal("143"), grams_per_piece=None, grams_per_ml=None)


def _item(item_id: int, product_id: int, quantity: str, unit_code: str) -> InventoryItemSnapshot:
    unit = find_measurement_unit(unit_code)
    assert unit is not None
    return InventoryItemSnapshot(
        id=item_id,
        product_id=product_id,
        household_id=HOME,
        product_name=f"produkt {product_id}",
        quantity=Decimal(quantity),
        unit=unit,
        minimum_quantity=None,
        photo_url=None,
    )


def _reader() -> FakeProductNutritionReader:
    return FakeProductNutritionReader(
        {
            FLOUR: SubjectNutrition(facts=FLOUR_FACTS, package=None),
            SALT: SubjectNutrition.untagged(),
            EGGS: SubjectNutrition(facts=EGG_FACTS, package=None),
        }
    )


def test_every_item_is_counted_from_one_catalog_lookup() -> None:
    reader = _reader()
    counter = InventoryCalorieCounter(reader)
    items = [_item(1, FLOUR, "2", "kg"), _item(2, SALT, "1", "kg"), _item(3, EGGS, "6", "szt")]

    listings = counter.count_many(HOME, items)

    assert reader.lookups == [(HOME, {FLOUR, SALT, EGGS})]
    assert [listing.item for listing in listings] == items
    assert listings[0].calories.kcal == Decimal("7280")
    assert listings[1].calories.uncounted_reason is TagGap.NO_TAG
    assert listings[2].calories.uncounted_reason is UncountedReason.NO_PIECE_WEIGHT


def test_a_single_item_is_counted_in_its_own_household() -> None:
    reader = _reader()
    counter = InventoryCalorieCounter(reader)

    listing = counter.count(_item(1, FLOUR, "500", "g"))

    assert reader.lookups == [(HOME, {FLOUR})]
    assert listing.calories.kcal == Decimal("1820")
    assert listing.calories.kcal_per_100g == Decimal("364")
