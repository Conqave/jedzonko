import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def ala() -> User:
    return User.objects.create_user(username="ala", password="Ma-Kota-1234")


def test_units_are_denied_for_anonymous_caller(api_client: APIClient) -> None:
    assert api_client.get("/api/units/").status_code == 403


def test_units_come_from_code_constants(api_client: APIClient, ala: User) -> None:
    api_client.force_login(ala)

    response = api_client.get("/api/units/")

    assert response.status_code == 200
    assert {unit["code"] for unit in response.data} == {"g", "kg", "ml", "l", "szt", "opak"}
    by_code = {unit["code"]: unit for unit in response.data}
    assert by_code["kg"] == {"code": "kg", "name": "kilogram", "dimension": "mass"}
    assert by_code["l"]["dimension"] == "volume"
    assert by_code["szt"]["dimension"] == "count"
