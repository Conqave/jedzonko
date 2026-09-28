import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Ingredient, Product
from households.models import Household
from recipes.models import Recipe, RecipeStep
from tests.factories import (
    add_recipe_line,
    confirm_ingredient,
    make_household,
    make_ingredient,
    make_product,
)


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
    return make_household(ala, "Dom Ali")


@pytest.fixture
def household_b(ola: User) -> Household:
    return make_household(ola, "Dom Oli")


@pytest.fixture
def flour_ingredient() -> Ingredient:
    return make_ingredient("Mąka pszenna")


@pytest.fixture
def sugar_ingredient() -> Ingredient:
    return make_ingredient("Cukier")


@pytest.fixture
def flour(ala: User, household_a: Household, flour_ingredient: Ingredient) -> Product:
    product = make_product(household_a, "Mąka pszenna", "kg")
    confirm_ingredient(ala, product, flour_ingredient)
    return product


@pytest.fixture
def sugar(ala: User, household_a: Household, sugar_ingredient: Ingredient) -> Product:
    product = make_product(household_a, "Cukier", "kg")
    confirm_ingredient(ala, product, sugar_ingredient)
    return product


@pytest.fixture
def foreign_flour(ola: User, household_b: Household, flour_ingredient: Ingredient) -> Product:
    product = make_product(household_b, "Mąka pszenna", "kg")
    confirm_ingredient(ola, product, flour_ingredient)
    return product


@pytest.fixture
def pancakes(ala: User, flour_ingredient: Ingredient, sugar_ingredient: Ingredient) -> Recipe:
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
    add_recipe_line(recipe, flour_ingredient, "Mąka pszenna", "500.000")
    add_recipe_line(recipe, sugar_ingredient, "Cukier", "100.000")
    return recipe
