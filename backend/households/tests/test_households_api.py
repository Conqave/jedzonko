import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from households.models import Household, HouseholdMembership

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


def _create_household(name: str, member: User) -> Household:
    household = Household.objects.create(name=name)
    HouseholdMembership.objects.create(household=household, user=member)
    return household


def test_household_list_is_denied_for_anonymous_caller(api_client: APIClient) -> None:
    assert api_client.get("/api/households/").status_code == 403


def test_user_sees_only_own_households(api_client: APIClient, ala: User, ola: User) -> None:
    _create_household("Dom Ali", ala)
    _create_household("Dom Oli", ola)
    api_client.force_login(ala)

    response = api_client.get("/api/households/")

    assert response.status_code == 200
    assert [item["name"] for item in response.data] == ["Dom Ali"]


def test_create_household_makes_creator_a_member(api_client: APIClient, ala: User) -> None:
    api_client.force_login(ala)

    response = api_client.post("/api/households/", {"name": "Nowy dom"}, format="json")

    assert response.status_code == 201
    assert response.data["member_count"] == 1
    assert HouseholdMembership.objects.filter(user=ala, household_id=response.data["id"]).exists()


def test_deleted_household_is_hidden(api_client: APIClient, ala: User) -> None:
    from django.utils import timezone

    household = _create_household("Stary dom", ala)
    Household.objects.filter(pk=household.pk).update(deleted_at=timezone.now())
    api_client.force_login(ala)

    assert api_client.get("/api/households/").data == []


def test_members_are_hidden_from_non_members(api_client: APIClient, ala: User, ola: User) -> None:
    household = _create_household("Dom Ali", ala)
    api_client.force_login(ola)

    response = api_client.get(f"/api/households/{household.pk}/members/")

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_member_can_add_and_remove_another_member(
    api_client: APIClient, ala: User, ola: User
) -> None:
    household = _create_household("Dom Ali", ala)
    api_client.force_login(ala)

    added = api_client.post(
        f"/api/households/{household.pk}/members/", {"username": "ola"}, format="json"
    )
    assert added.status_code == 201

    removed = api_client.delete(f"/api/households/{household.pk}/members/{ola.pk}/")
    assert removed.status_code == 204
    assert not HouseholdMembership.objects.filter(household=household, user=ola).exists()


def test_adding_unknown_user_is_not_found(api_client: APIClient, ala: User) -> None:
    household = _create_household("Dom Ali", ala)
    api_client.force_login(ala)

    response = api_client.post(
        f"/api/households/{household.pk}/members/", {"username": "nieznany"}, format="json"
    )

    assert response.status_code == 404
    assert response.data["code"] == "user_not_found"


def test_last_member_cannot_be_removed(api_client: APIClient, ala: User) -> None:
    household = _create_household("Dom Ali", ala)
    api_client.force_login(ala)

    response = api_client.delete(f"/api/households/{household.pk}/members/{ala.pk}/")

    assert response.status_code == 400
    assert response.data["code"] == "last_member_cannot_leave"


def test_member_count_reflects_every_member(api_client: APIClient, ala: User, ola: User) -> None:
    household = _create_household("Wspólny dom", ala)
    HouseholdMembership.objects.create(household=household, user=ola)
    api_client.force_login(ala)

    response = api_client.get("/api/households/")

    assert [(item["name"], item["member_count"]) for item in response.data] == [("Wspólny dom", 2)]


def test_member_renames_a_household(api_client: APIClient, ala: User) -> None:
    household = _create_household("Stara nazwa", ala)
    api_client.force_login(ala)

    response = api_client.patch(
        f"/api/households/{household.pk}/", {"name": "Nowa nazwa"}, format="json"
    )

    assert response.status_code == 200
    assert response.data == {"id": household.pk, "name": "Nowa nazwa", "member_count": 1}
    household.refresh_from_db()
    assert household.name == "Nowa nazwa"


def test_non_member_cannot_rename_a_household(api_client: APIClient, ala: User, ola: User) -> None:
    household = _create_household("Dom Ali", ala)
    api_client.force_login(ola)

    response = api_client.patch(
        f"/api/households/{household.pk}/", {"name": "Przejęty dom"}, format="json"
    )

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"
    household.refresh_from_db()
    assert household.name == "Dom Ali"


def test_renaming_requires_a_name(api_client: APIClient, ala: User) -> None:
    household = _create_household("Dom Ali", ala)
    api_client.force_login(ala)

    response = api_client.patch(f"/api/households/{household.pk}/", {"name": "  "}, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "invalid"


def test_renaming_a_deleted_household_is_not_found(api_client: APIClient, ala: User) -> None:
    from django.utils import timezone

    household = _create_household("Dom Ali", ala)
    Household.objects.filter(pk=household.pk).update(deleted_at=timezone.now())
    api_client.force_login(ala)

    response = api_client.patch(f"/api/households/{household.pk}/", {"name": "Nowa"}, format="json")

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_a_new_household_starts_with_its_primary_shopping_list(
    api_client: APIClient, ala: User
) -> None:
    api_client.force_login(ala)

    created = api_client.post("/api/households/", {"name": "Nowy dom"}, format="json")
    lists = api_client.get(f"/api/shopping/lists/?household_id={created.data['id']}")

    assert created.status_code == 201
    assert [(item["name"], item["is_primary"]) for item in lists.data] == [("Lista zakupów", True)]
