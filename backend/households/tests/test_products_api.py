import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from households.models import Household, HouseholdMembership, Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def ala() -> User:
    return User.objects.create_user(username="ala", password="Ma-Kota-1234")


@pytest.fixture
def ola() -> User:
    return User.objects.create_user(username="ola", password="Ma-Psa-1234")


@pytest.fixture
def household(ala: User) -> Household:
    created = Household.objects.create(name="Dom Ali")
    HouseholdMembership.objects.create(household=created, user=ala)
    return created


@pytest.fixture
def other_household(ola: User) -> Household:
    created = Household.objects.create(name="Dom Oli")
    HouseholdMembership.objects.create(household=created, user=ola)
    return created


def test_products_are_denied_for_anonymous_caller(api_client: APIClient) -> None:
    assert api_client.get("/api/products/", {"household_id": 1}).status_code == 403
    assert api_client.post("/api/products/", {}, format="json").status_code == 403


def test_member_creates_and_lists_a_product(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)

    created = api_client.post(
        "/api/products/",
        {
            "household_id": household.pk,
            "name": "Mąka pszenna",
            "default_unit_code": "kg",
            "is_food": True,
        },
        format="json",
    )

    assert created.status_code == 201
    assert created.data["name"] == "Mąka pszenna"
    assert created.data["household_id"] == household.pk
    assert created.data["default_unit_code"] == "kg"
    assert created.data["is_food"] is True

    listed = api_client.get("/api/products/", {"household_id": household.pk})
    assert [item["id"] for item in listed.data] == [created.data["id"]]


def test_search_ignores_polish_diacritics(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)
    api_client.post(
        "/api/products/",
        {"household_id": household.pk, "name": "Mąka pszenna", "default_unit_code": "kg"},
        format="json",
    )

    listed = api_client.get("/api/products/", {"household_id": str(household.pk), "search": "mak"})

    assert [item["name"] for item in listed.data] == ["Mąka pszenna"]


def test_the_same_normalized_name_cannot_be_created_twice(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)
    payload = {"household_id": household.pk, "name": "Mąka pszenna", "default_unit_code": "kg"}
    api_client.post("/api/products/", payload, format="json")

    response = api_client.post(
        "/api/products/",
        {"household_id": household.pk, "name": "MAKA PSZENNA", "default_unit_code": "kg"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "duplicate_product"


def test_two_households_own_independent_products(
    api_client: APIClient, ala: User, ola: User, household: Household, other_household: Household
) -> None:
    api_client.force_login(ala)
    api_client.post(
        "/api/products/",
        {"household_id": household.pk, "name": "Mąka pszenna", "default_unit_code": "kg"},
        format="json",
    )
    api_client.logout()
    api_client.force_login(ola)

    created = api_client.post(
        "/api/products/",
        {"household_id": other_household.pk, "name": "Mąka pszenna", "default_unit_code": "kg"},
        format="json",
    )

    assert created.status_code == 201
    assert Product.objects.filter(normalized_name="maka pszenna").count() == 2
    listed = api_client.get("/api/products/", {"household_id": other_household.pk})
    assert [item["id"] for item in listed.data] == [created.data["id"]]


def test_unknown_unit_is_rejected(api_client: APIClient, ala: User, household: Household) -> None:
    api_client.force_login(ala)

    response = api_client.post(
        "/api/products/",
        {"household_id": household.pk, "name": "Mąka", "default_unit_code": "parsek"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "measurement_unit_not_found"


def test_non_member_can_neither_read_nor_create(
    api_client: APIClient, ola: User, household: Household
) -> None:
    api_client.force_login(ola)

    assert (
        api_client.get("/api/products/", {"household_id": household.pk}).data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.post(
            "/api/products/",
            {"household_id": household.pk, "name": "Mąka", "default_unit_code": "kg"},
            format="json",
        ).data["code"]
        == "not_a_household_member"
    )
