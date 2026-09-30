from decimal import Decimal

import pytest

from catalog.application.errors import DuplicateProductError, ProductNotFoundError
from catalog.application.use_cases.create_product import CreateProduct
from catalog.application.use_cases.delete_product import DeleteProduct
from catalog.application.use_cases.list_household_products import ListHouseholdProducts
from catalog.application.use_cases.update_product import UpdateProduct
from catalog.domain.errors import UnknownMeasurementUnitError
from catalog.domain.product import ProductPackage
from catalog.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeProductRepository,
    FakeTransactionManager,
)
from shared.household_membership import NotAHouseholdMemberError

MEMBER = 1
STRANGER = 2
HOUSEHOLD = 10


@pytest.fixture
def products() -> FakeProductRepository:
    return FakeProductRepository()


@pytest.fixture
def memberships() -> FakeHouseholdMembershipReader:
    return FakeHouseholdMembershipReader({(MEMBER, HOUSEHOLD)})


@pytest.fixture
def transactions() -> FakeTransactionManager:
    return FakeTransactionManager()


def test_creating_a_product_stores_its_parsed_name(
    products: FakeProductRepository,
    memberships: FakeHouseholdMembershipReader,
    transactions: FakeTransactionManager,
) -> None:
    package = ProductPackage(quantity=Decimal("500"), unit_code="g")

    product = CreateProduct(products, memberships, transactions).execute(
        MEMBER, HOUSEHOLD, " Mąka ", "g", True, package
    )

    assert product.name == "Mąka"
    assert product.package == package
    assert products.find(product.id) == product
    assert transactions.opened == 1


def test_creating_a_duplicate_product_is_rejected(
    products: FakeProductRepository,
    memberships: FakeHouseholdMembershipReader,
    transactions: FakeTransactionManager,
) -> None:
    products.add(HOUSEHOLD, "Mąka")

    with pytest.raises(DuplicateProductError):
        CreateProduct(products, memberships, transactions).execute(
            MEMBER, HOUSEHOLD, "mąka", "g", True, None
        )


def test_creating_a_product_with_an_unknown_unit_is_rejected(
    products: FakeProductRepository,
    memberships: FakeHouseholdMembershipReader,
    transactions: FakeTransactionManager,
) -> None:
    with pytest.raises(UnknownMeasurementUnitError):
        CreateProduct(products, memberships, transactions).execute(
            MEMBER, HOUSEHOLD, "Mąka", "parsec", True, None
        )


def test_a_stranger_cannot_create_a_product(
    products: FakeProductRepository,
    memberships: FakeHouseholdMembershipReader,
    transactions: FakeTransactionManager,
) -> None:
    with pytest.raises(NotAHouseholdMemberError):
        CreateProduct(products, memberships, transactions).execute(
            STRANGER, HOUSEHOLD, "Mąka", "g", True, None
        )

    assert products.products == {}


def test_updating_a_product_renames_it(
    products: FakeProductRepository,
    memberships: FakeHouseholdMembershipReader,
    transactions: FakeTransactionManager,
) -> None:
    product = products.add(HOUSEHOLD, "Mąka")

    updated = UpdateProduct(products, memberships, transactions).execute(
        MEMBER, product.id, "Mąka tortowa", None
    )

    assert updated.name == "Mąka tortowa"


def test_updating_a_product_keeps_its_own_name_available(
    products: FakeProductRepository,
    memberships: FakeHouseholdMembershipReader,
    transactions: FakeTransactionManager,
) -> None:
    product = products.add(HOUSEHOLD, "Mąka")

    updated = UpdateProduct(products, memberships, transactions).execute(
        MEMBER, product.id, "MĄKA", None
    )

    assert updated.name == "MĄKA"


def test_updating_to_another_products_name_is_rejected(
    products: FakeProductRepository,
    memberships: FakeHouseholdMembershipReader,
    transactions: FakeTransactionManager,
) -> None:
    products.add(HOUSEHOLD, "Mąka")
    sugar = products.add(HOUSEHOLD, "Cukier")

    with pytest.raises(DuplicateProductError):
        UpdateProduct(products, memberships, transactions).execute(MEMBER, sugar.id, "Mąka", None)


def test_updating_a_missing_product_is_rejected(
    products: FakeProductRepository,
    memberships: FakeHouseholdMembershipReader,
    transactions: FakeTransactionManager,
) -> None:
    with pytest.raises(ProductNotFoundError):
        UpdateProduct(products, memberships, transactions).execute(MEMBER, 99, "Mąka", None)


def test_deleting_a_product_removes_it(
    products: FakeProductRepository, memberships: FakeHouseholdMembershipReader
) -> None:
    product = products.add(HOUSEHOLD, "Mąka")

    DeleteProduct(products, memberships).execute(MEMBER, product.id)

    assert products.find(product.id) is None


def test_a_stranger_cannot_delete_a_product(
    products: FakeProductRepository, memberships: FakeHouseholdMembershipReader
) -> None:
    product = products.add(HOUSEHOLD, "Mąka")

    with pytest.raises(NotAHouseholdMemberError):
        DeleteProduct(products, memberships).execute(STRANGER, product.id)

    assert products.find(product.id) == product


def test_deleting_a_missing_product_is_rejected(
    products: FakeProductRepository, memberships: FakeHouseholdMembershipReader
) -> None:
    with pytest.raises(ProductNotFoundError):
        DeleteProduct(products, memberships).execute(MEMBER, 99)


def test_listing_products_filters_by_the_normalized_search(
    products: FakeProductRepository, memberships: FakeHouseholdMembershipReader
) -> None:
    flour = products.add(HOUSEHOLD, "Mąka")
    products.add(HOUSEHOLD, "Cukier")

    listings = ListHouseholdProducts(products, memberships).execute(MEMBER, HOUSEHOLD, " MĄK ")

    assert [listing.product for listing in listings] == [flour]


def test_listing_products_treats_a_blank_search_as_no_filter(
    products: FakeProductRepository, memberships: FakeHouseholdMembershipReader
) -> None:
    products.add(HOUSEHOLD, "Mąka")
    products.add(HOUSEHOLD, "Cukier")

    listings = ListHouseholdProducts(products, memberships).execute(MEMBER, HOUSEHOLD, "  ")

    assert len(listings) == 2
