from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from catalog.models import Product
from households.domain.retention import HOUSEHOLD_RETENTION_PERIOD
from households.models import Household
from inventory.models import InventoryItem
from shopping.models import ShoppingList, ShoppingListItem
from tests.factories import make_household, make_product

pytestmark = pytest.mark.django_db


@pytest.fixture
def household(ala: User) -> Household:
    created = make_household(ala, "Dom Ali")
    product = make_product(created, "Mąka pszenna", "kg")
    InventoryItem.objects.create(product=product, unit_code="kg", quantity=Decimal("2.000"))
    shopping_list = ShoppingList.objects.create(household=created, name="Zakupy")
    ShoppingListItem.objects.create(
        shopping_list=shopping_list,
        product=product,
        unit_code="kg",
        quantity=Decimal("1.000"),
        status="pending",
    )
    return created


def _set_deleted_at_days_ago(household_id: int, days: int) -> None:
    Household.objects.filter(pk=household_id).update(
        deleted_at=timezone.now() - timedelta(days=days)
    )


def test_member_deletes_a_household_and_stops_seeing_it(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)

    response = api_client.delete(f"/api/households/{household.pk}/")

    assert response.status_code == 204
    assert api_client.get("/api/households/").data == []
    household.refresh_from_db()
    assert household.deleted_at is not None


def test_deleted_household_stops_answering_inventory_and_shopping(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)
    api_client.delete(f"/api/households/{household.pk}/")

    inventory = api_client.get(f"/api/inventory/?household_id={household.pk}")
    shopping = api_client.get(f"/api/shopping/lists/?household_id={household.pk}")
    products = api_client.get(f"/api/products/?household_id={household.pk}")

    assert inventory.status_code == 403
    assert inventory.data["code"] == "not_a_household_member"
    assert shopping.status_code == 403
    assert products.status_code == 403


def test_non_member_cannot_delete_a_household(
    api_client: APIClient, ola: User, household: Household
) -> None:
    api_client.force_login(ola)

    response = api_client.delete(f"/api/households/{household.pk}/")

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"
    household.refresh_from_db()
    assert household.deleted_at is None


def test_deleting_an_already_deleted_household_is_not_found(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)
    api_client.delete(f"/api/households/{household.pk}/")

    response = api_client.delete(f"/api/households/{household.pk}/")

    assert response.status_code == 404
    assert response.data["code"] == "household_not_found"


def test_member_lists_deleted_households(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)
    api_client.delete(f"/api/households/{household.pk}/")

    response = api_client.get("/api/households/deleted/")

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [household.pk]
    assert response.data[0]["purge_after"] > response.data[0]["deleted_at"]


def test_non_member_does_not_list_foreign_deleted_households(
    api_client: APIClient, ala: User, ola: User, household: Household
) -> None:
    api_client.force_login(ala)
    api_client.delete(f"/api/households/{household.pk}/")
    api_client.force_login(ola)

    assert api_client.get("/api/households/deleted/").data == []


def test_restore_inside_the_window_brings_the_household_back_with_its_data(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)
    api_client.delete(f"/api/households/{household.pk}/")
    _set_deleted_at_days_ago(household.pk, HOUSEHOLD_RETENTION_PERIOD.days - 1)

    response = api_client.post(f"/api/households/{household.pk}/restore/")

    assert response.status_code == 200
    assert response.data["id"] == household.pk
    assert [item["id"] for item in api_client.get("/api/households/").data] == [household.pk]
    assert len(api_client.get(f"/api/inventory/?household_id={household.pk}").data) == 1
    assert len(api_client.get(f"/api/products/?household_id={household.pk}").data) == 1


def test_a_restored_household_returns_to_its_place_in_creation_order(
    api_client: APIClient, ala: User, household: Household
) -> None:
    earlier = make_household(ala, "Zakupy wspólne")
    later = make_household(ala, "Ania testuje")
    Household.objects.filter(pk=earlier.pk).update(
        created_at=household.created_at - timedelta(days=1)
    )
    api_client.force_login(ala)
    api_client.delete(f"/api/households/{household.pk}/")

    api_client.post(f"/api/households/{household.pk}/restore/")

    listed = api_client.get("/api/households/").data
    assert [item["id"] for item in listed] == [earlier.pk, household.pk, later.pk]


def test_restore_outside_the_window_is_rejected(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)
    api_client.delete(f"/api/households/{household.pk}/")
    _set_deleted_at_days_ago(household.pk, HOUSEHOLD_RETENTION_PERIOD.days + 1)

    response = api_client.post(f"/api/households/{household.pk}/restore/")

    assert response.status_code == 400
    assert response.data["code"] == "recovery_window_expired"
    assert api_client.get("/api/households/").data == []


def test_non_member_cannot_restore_a_household(
    api_client: APIClient, ala: User, ola: User, household: Household
) -> None:
    api_client.force_login(ala)
    api_client.delete(f"/api/households/{household.pk}/")
    api_client.force_login(ola)

    response = api_client.post(f"/api/households/{household.pk}/restore/")

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_restoring_a_live_household_is_not_found(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)

    response = api_client.post(f"/api/households/{household.pk}/restore/")

    assert response.status_code == 404
    assert response.data["code"] == "household_not_found"


def test_purge_command_removes_expired_households_with_their_data(household: Household) -> None:
    _set_deleted_at_days_ago(household.pk, HOUSEHOLD_RETENTION_PERIOD.days + 1)
    output = StringIO()

    call_command("purge_deleted_households", stdout=output)

    assert not Household.objects.filter(pk=household.pk).exists()
    assert not Product.objects.filter(household_id=household.pk).exists()
    assert not InventoryItem.objects.filter(product__household_id=household.pk).exists()
    assert not ShoppingList.objects.filter(household_id=household.pk).exists()
    assert not ShoppingListItem.objects.exists()
    assert "Purged 1 household(s)." in output.getvalue()
    assert "Dom Ali" in output.getvalue()


def test_purge_command_leaves_fresh_and_live_households_alone(
    ala: User, household: Household
) -> None:
    fresh = make_household(ala, "Swiezo skasowany")
    _set_deleted_at_days_ago(fresh.pk, HOUSEHOLD_RETENTION_PERIOD.days - 1)
    output = StringIO()

    call_command("purge_deleted_households", stdout=output)

    assert Household.objects.filter(pk=fresh.pk).exists()
    assert Household.objects.filter(pk=household.pk).exists()
    assert "Purged 0 household(s)." in output.getvalue()


def test_purge_command_dry_run_changes_nothing(household: Household) -> None:
    _set_deleted_at_days_ago(household.pk, HOUSEHOLD_RETENTION_PERIOD.days + 1)
    output = StringIO()

    call_command("purge_deleted_households", "--dry-run", stdout=output)

    assert Household.objects.filter(pk=household.pk).exists()
    assert Product.objects.filter(household_id=household.pk).count() == 1
    assert InventoryItem.objects.filter(product__household_id=household.pk).count() == 1
    assert "Would purge 1 household(s)." in output.getvalue()
