from collections.abc import Iterator
from contextlib import contextmanager

import httpx
from django.conf import settings

from households.composition import build_household_access_policy
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.application.ports.recipe_source import RecipeSource
from recipes.application.ports.transaction_manager import TransactionManager
from recipes.application.use_cases.calculate_missing_recipe_items import CalculateMissingRecipeItems
from recipes.application.use_cases.confirm_recipe_preparation import ConfirmRecipePreparation
from recipes.application.use_cases.create_recipe import CreateRecipe
from recipes.application.use_cases.delete_recipe import DeleteRecipe
from recipes.application.use_cases.get_external_recipe import GetExternalRecipe
from recipes.application.use_cases.get_recipe import GetRecipe
from recipes.application.use_cases.list_recipes import ListRecipes
from recipes.application.use_cases.search_external_recipes import SearchExternalRecipes
from recipes.application.use_cases.suggest_external_recipes_from_inventory import (
    SuggestExternalRecipesFromInventory,
)
from recipes.application.use_cases.suggest_recipes_from_inventory import SuggestRecipesFromInventory
from recipes.application.use_cases.update_recipe import UpdateRecipe
from recipes.infrastructure.django_recipe_repository import DjangoRecipeRepository
from recipes.infrastructure.django_transaction_manager import DjangoTransactionManager
from recipes.infrastructure.inventory_household_inventory_consumer import (
    InventoryHouseholdInventoryConsumer,
)
from recipes.infrastructure.inventory_household_inventory_reader import (
    InventoryHouseholdInventoryReader,
)
from recipes.infrastructure.providers.ania_gotuje.provider import AniaGotujeProvider


def build_recipe_repository() -> RecipeRepository:
    return DjangoRecipeRepository()


def build_household_inventory_reader() -> HouseholdInventoryReader:
    return InventoryHouseholdInventoryReader()


def build_list_recipes() -> ListRecipes:
    return ListRecipes(build_recipe_repository())


def build_get_recipe() -> GetRecipe:
    return GetRecipe(build_recipe_repository())


def build_create_recipe() -> CreateRecipe:
    return CreateRecipe(build_recipe_repository())


def build_update_recipe() -> UpdateRecipe:
    return UpdateRecipe(build_recipe_repository())


def build_delete_recipe() -> DeleteRecipe:
    return DeleteRecipe(build_recipe_repository())


def build_suggest_recipes_from_inventory() -> SuggestRecipesFromInventory:
    return SuggestRecipesFromInventory(
        build_recipe_repository(),
        build_household_inventory_reader(),
        build_household_access_policy(),
    )


def build_calculate_missing_recipe_items() -> CalculateMissingRecipeItems:
    return CalculateMissingRecipeItems(
        build_recipe_repository(),
        build_household_inventory_reader(),
        build_household_access_policy(),
    )


def build_household_inventory_consumer() -> HouseholdInventoryConsumer:
    return InventoryHouseholdInventoryConsumer()


def build_transaction_manager() -> TransactionManager:
    return DjangoTransactionManager()


def build_confirm_recipe_preparation() -> ConfirmRecipePreparation:
    return ConfirmRecipePreparation(
        build_recipe_repository(),
        build_household_inventory_reader(),
        build_household_inventory_consumer(),
        build_transaction_manager(),
        build_household_access_policy(),
    )


@contextmanager
def open_recipe_source() -> Iterator[RecipeSource]:
    with httpx.Client(
        timeout=httpx.Timeout(settings.RECIPE_SOURCE_HTTP_TIMEOUT_SECONDS),
        headers={"User-Agent": settings.RECIPE_SOURCE_HTTP_USER_AGENT},
        follow_redirects=True,
    ) as client:
        yield AniaGotujeProvider(client)


def build_get_external_recipe(source: RecipeSource) -> GetExternalRecipe:
    return GetExternalRecipe(source)


def build_search_external_recipes(source: RecipeSource) -> SearchExternalRecipes:
    return SearchExternalRecipes(
        source, build_household_inventory_reader(), build_household_access_policy()
    )


def build_suggest_external_recipes_from_inventory(
    source: RecipeSource,
) -> SuggestExternalRecipesFromInventory:
    return SuggestExternalRecipesFromInventory(
        source,
        build_household_inventory_reader(),
        build_household_access_policy(),
        settings.RECIPE_SOURCE_SUGGESTION_INGREDIENT_LIMIT,
    )
