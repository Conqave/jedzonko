from datetime import UTC, datetime
from decimal import Decimal

import pytest

from catalog.application.use_cases.describe_household_products import DescribeHouseholdProducts
from catalog.application.use_cases.get_product_nutrition import GetProductNutrition
from catalog.domain.calories import TagCalories
from catalog.domain.conversions import PieceWeight
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.domain.product import ProductPackage
from catalog.domain.product_ingredient import (
    ProductIngredient,
    ProductIngredientSource,
    ProductIngredientStatus,
)
from catalog.tests.fakes import (
    FakeIngredientRepository,
    FakeProductClassificationRepository,
    FakeProductRepository,
    FakeTransactionManager,
)
from shared.item_calories import SubjectNutrition, TagGap
from shared.measurement_units import find_measurement_unit
from shared.nutrition import NutritionFacts

HOME = 10
NOW = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


class Catalog:
    def __init__(self) -> None:
        self.transactions = FakeTransactionManager()
        self.products = FakeProductRepository()
        self.ingredients = FakeIngredientRepository()
        self.classifications = FakeProductClassificationRepository(self.transactions)

    def product(self, name: str, package: ProductPackage | None = None) -> int:
        product_name = CatalogName.parse(name)
        product = self.products.create(HOME, product_name, "szt", True, package)
        self.classifications.add_product(product.id, HOME)
        return product.id

    def tag(self, name: str, kcal_per_100g: str | None) -> int:
        tag_name = CatalogName.parse(name)
        ingredient = self.ingredients.create(tag_name, IngredientNameSource.MANUAL)
        calories = None if kcal_per_100g is None else TagCalories.manual(Decimal(kcal_per_100g))
        self.ingredients.save_calories(ingredient.id, calories)
        return ingredient.id

    def confirm(self, product_id: int, ingredient_id: int) -> None:
        link = ProductIngredient(
            product_id=product_id,
            ingredient_id=ingredient_id,
            status=ProductIngredientStatus.CONFIRMED,
            source=ProductIngredientSource.MANUAL,
            model_name=None,
            proposed_at=None,
            decided_at=NOW,
        )
        with self.transactions.atomic():
            self.classifications.save((link,))

    def nutrition(self, product_ids: set[int]) -> dict[int, SubjectNutrition]:
        describe = DescribeHouseholdProducts(self.products, self.classifications, self.ingredients)
        use_case = GetProductNutrition(describe, self.ingredients)
        return use_case.execute(HOME, product_ids)


@pytest.fixture
def catalog() -> Catalog:
    return Catalog()


def test_a_product_takes_the_nutrition_facts_of_its_only_tag(catalog: Catalog) -> None:
    milk = catalog.product("Mleko 3,2%")
    milk_tag = catalog.tag("mleko", "64")
    catalog.ingredients.save_piece_weight(milk_tag, PieceWeight.manual(Decimal("1030")))
    catalog.confirm(milk, milk_tag)

    nutrition = catalog.nutrition({milk})

    facts = NutritionFacts(
        kcal_per_100g=Decimal("64"), grams_per_piece=Decimal("1030"), grams_per_ml=None
    )
    assert nutrition == {milk: SubjectNutrition(facts=facts, package=None)}


def test_a_product_without_a_confirmed_tag_has_no_facts(catalog: Catalog) -> None:
    salt = catalog.product("Sól")

    nutrition = catalog.nutrition({salt})

    assert nutrition[salt].facts is TagGap.NO_TAG


def test_a_product_with_several_tags_has_no_facts_rather_than_a_guess(catalog: Catalog) -> None:
    mix = catalog.product("Mieszanka studencka")
    catalog.confirm(mix, catalog.tag("orzechy", "650"))
    catalog.confirm(mix, catalog.tag("rodzynki", "300"))

    nutrition = catalog.nutrition({mix})

    assert nutrition[mix].facts is TagGap.SEVERAL_TAGS


def test_a_tag_without_calories_still_reports_its_other_facts(catalog: Catalog) -> None:
    water = catalog.product("Woda")
    catalog.confirm(water, catalog.tag("woda", None))

    nutrition = catalog.nutrition({water})

    assert nutrition[water].facts == NutritionFacts(
        kcal_per_100g=None, grams_per_piece=None, grams_per_ml=None
    )


def test_a_package_comes_with_the_product_as_a_quantity(catalog: Catalog) -> None:
    package = ProductPackage(quantity=Decimal("500"), unit_code="g")
    pasta = catalog.product("Makaron", package)
    catalog.confirm(pasta, catalog.tag("makaron", "350"))

    nutrition = catalog.nutrition({pasta})

    package_quantity = nutrition[pasta].package
    assert package_quantity is not None
    assert package_quantity.amount == Decimal("500")
    assert package_quantity.unit == find_measurement_unit("g")


def test_asking_for_no_products_reads_nothing(catalog: Catalog) -> None:
    assert catalog.nutrition(set()) == {}
