from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from households.models import Household, HouseholdMembership, Product
from recipes.models import Recipe, RecipeIngredient, RecipeStep
from shared.text import normalize_text


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
def household_a(ala: User) -> Household:
    household = Household.objects.create(name="Dom Ali")
    HouseholdMembership.objects.create(household=household, user=ala)
    return household


@pytest.fixture
def household_b(ola: User) -> Household:
    household = Household.objects.create(name="Dom Oli")
    HouseholdMembership.objects.create(household=household, user=ola)
    return household


def make_product(household: Household, name: str, default_unit_code: str) -> Product:
    return Product.objects.create(
        household=household,
        name=name,
        normalized_name=normalize_text(name),
        default_unit_code=default_unit_code,
        is_food=True,
    )


@pytest.fixture
def flour(household_a: Household) -> Product:
    return make_product(household_a, "Mąka pszenna", "kg")


@pytest.fixture
def sugar(household_a: Household) -> Product:
    return make_product(household_a, "Cukier", "kg")


@pytest.fixture
def foreign_flour(household_b: Household) -> Product:
    return make_product(household_b, "Mąka pszenna", "kg")


@pytest.fixture
def pancakes(ala: User) -> Recipe:
    recipe = Recipe.objects.create(
        name="Naleśniki",
        description="Podstawowe naleśniki.",
        servings=4,
        preparation_time_minutes=10,
        cooking_time_minutes=15,
        difficulty="easy",
        created_by=ala,
    )
    RecipeStep.objects.create(recipe=recipe, position=1, text="Wymieszaj składniki.")
    RecipeIngredient.objects.create(
        recipe=recipe,
        name="Mąka pszenna",
        normalized_name=normalize_text("Mąka pszenna"),
        unit_code="g",
        quantity=Decimal("500.000"),
    )
    RecipeIngredient.objects.create(
        recipe=recipe,
        name="Cukier",
        normalized_name=normalize_text("Cukier"),
        unit_code="g",
        quantity=Decimal("100.000"),
    )
    return recipe
