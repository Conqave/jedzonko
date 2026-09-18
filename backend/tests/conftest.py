from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Ingredient, MeasurementUnit
from households.models import Household, HouseholdMembership
from recipes.models import Recipe, RecipeIngredient, RecipeStep


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


@pytest.fixture
def gram() -> MeasurementUnit:
    return MeasurementUnit.objects.get(code="g")


@pytest.fixture
def kilogram() -> MeasurementUnit:
    return MeasurementUnit.objects.get(code="kg")


@pytest.fixture
def flour(kilogram: MeasurementUnit) -> Ingredient:
    return Ingredient.objects.create(name="Mąka pszenna", default_unit=kilogram)


@pytest.fixture
def sugar(kilogram: MeasurementUnit) -> Ingredient:
    return Ingredient.objects.create(name="Cukier", default_unit=kilogram)


@pytest.fixture
def pancakes(ala: User, flour: Ingredient, sugar: Ingredient, gram: MeasurementUnit) -> Recipe:
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
        recipe=recipe, ingredient=flour, unit=gram, quantity=Decimal("500.000")
    )
    RecipeIngredient.objects.create(
        recipe=recipe, ingredient=sugar, unit=gram, quantity=Decimal("100.000")
    )
    return recipe
