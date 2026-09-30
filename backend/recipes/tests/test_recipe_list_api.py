from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from config.composition import container
from tests.factories import make_ingredient

pytestmark = pytest.mark.django_db


@pytest.fixture
def member_client(ala: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(ala)
    return client


def _create(client: APIClient, name: str, servings: int) -> None:
    body = {
        "name": name,
        "description": "",
        "servings": servings,
        "preparation_time_minutes": 5,
        "cooking_time_minutes": 5,
        "difficulty": "easy",
        "tag_names": [],
        "steps": [{"position": 1, "text": "gotuj"}],
        "ingredients": [
            {"name": "Jajko", "quantity": "200", "unit_code": "g"},
            {"name": "szczypiorek", "quantity": "5", "unit_code": "g"},
        ],
    }
    response = client.post("/api/recipes/", body, format="json")
    assert response.status_code == 201, response.data


def test_the_list_shows_calories_and_ingredient_names(member_client: APIClient) -> None:
    eggs = make_ingredient("jajko")
    container().catalog.set_tag_calories.execute(eggs.pk, Decimal("143"))
    _create(member_client, "omlet", 2)

    response = member_client.get("/api/recipes/")

    assert response.status_code == 200
    listed = response.data[0]
    assert listed["nutrition"] == {
        "total_kcal": "286.0",
        "kcal_per_serving": "143.0",
        "has_estimates": False,
        "uncounted_ingredients": [{"name": "szczypiorek", "reason": "no_calories"}],
    }
    assert listed["ingredient_names"] == ["Jajko", "jajko", "szczypiorek"]


def test_the_list_reads_in_a_fixed_number_of_queries(member_client: APIClient) -> None:
    make_ingredient("jajko")
    _create(member_client, "omlet", 2)
    with CaptureQueriesContext(connection) as single:
        member_client.get("/api/recipes/")
    _create(member_client, "jajecznica", 1)
    _create(member_client, "szakszuka", 3)

    with CaptureQueriesContext(connection) as several:
        member_client.get("/api/recipes/")

    assert len(several.captured_queries) == len(single.captured_queries)
