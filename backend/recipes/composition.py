from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import httpx

from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from recipes.application.use_cases.calculate_external_recipe_shortfall import (
    CalculateExternalRecipeShortfall,
)
from recipes.application.use_cases.calculate_missing_recipe_items import (
    CalculateMissingRecipeItems,
)
from recipes.application.use_cases.confirm_recipe_preparation import ConfirmRecipePreparation
from recipes.application.use_cases.create_recipe import CreateRecipe
from recipes.application.use_cases.delete_recipe import DeleteRecipe
from recipes.application.use_cases.external_recipes import ExternalRecipes
from recipes.application.use_cases.get_external_recipe import GetExternalRecipe
from recipes.application.use_cases.get_recipe import GetRecipe
from recipes.application.use_cases.list_recipes import ListRecipes
from recipes.application.use_cases.reassign_recipe_ingredient import ReassignRecipeIngredient
from recipes.application.use_cases.search_external_recipes import SearchExternalRecipes
from recipes.application.use_cases.suggest_external_recipes_from_inventory import (
    SuggestExternalRecipesFromInventory,
)
from recipes.application.use_cases.suggest_recipes_from_inventory import (
    SuggestRecipesFromInventory,
)
from recipes.application.use_cases.update_recipe import UpdateRecipe
from recipes.infrastructure.django_recipe_repository import DjangoRecipeRepository
from recipes.infrastructure.providers.ania_gotuje.provider import AniaGotujeProvider
from shared.household_membership import HouseholdMembershipReader
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class RecipeSourceSettings:
    timeout_seconds: float
    user_agent: str
    suggestion_ingredient_limit: int


@dataclass(frozen=True, slots=True)
class RecipesModule:
    list_recipes: ListRecipes
    get_recipe: GetRecipe
    create_recipe: CreateRecipe
    update_recipe: UpdateRecipe
    delete_recipe: DeleteRecipe
    suggest_recipes_from_inventory: SuggestRecipesFromInventory
    calculate_missing_recipe_items: CalculateMissingRecipeItems
    confirm_recipe_preparation: ConfirmRecipePreparation
    reassign_recipe_ingredient: ReassignRecipeIngredient
    stock: HouseholdStockReader
    resolver: IngredientResolver
    memberships: HouseholdMembershipReader
    source_settings: RecipeSourceSettings

    @contextmanager
    def open_external(self) -> Iterator[ExternalRecipes]:
        settings = self.source_settings
        with httpx.Client(
            timeout=httpx.Timeout(settings.timeout_seconds),
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        ) as client:
            source = AniaGotujeProvider(client)
            yield ExternalRecipes(
                search=SearchExternalRecipes(source, self.stock, self.resolver, self.memberships),
                suggest_from_inventory=SuggestExternalRecipesFromInventory(
                    source,
                    self.stock,
                    self.resolver,
                    self.memberships,
                    settings.suggestion_ingredient_limit,
                ),
                get=GetExternalRecipe(source),
                calculate_shortfall=CalculateExternalRecipeShortfall(
                    source, self.stock, self.resolver, self.memberships
                ),
            )


def build_reassign_recipe_ingredient() -> ReassignRecipeIngredient:
    return ReassignRecipeIngredient(DjangoRecipeRepository())


def build_recipes(
    memberships: HouseholdMembershipReader,
    stock: HouseholdStockReader,
    resolver: IngredientResolver,
    consumer: HouseholdInventoryConsumer,
    reassign_recipe_ingredient: ReassignRecipeIngredient,
    source_settings: RecipeSourceSettings,
    transactions: TransactionManager,
) -> RecipesModule:
    recipes = DjangoRecipeRepository()
    return RecipesModule(
        list_recipes=ListRecipes(recipes),
        get_recipe=GetRecipe(recipes),
        create_recipe=CreateRecipe(recipes, resolver, transactions),
        update_recipe=UpdateRecipe(recipes, resolver, transactions),
        delete_recipe=DeleteRecipe(recipes),
        suggest_recipes_from_inventory=SuggestRecipesFromInventory(recipes, stock, memberships),
        calculate_missing_recipe_items=CalculateMissingRecipeItems(recipes, stock, memberships),
        confirm_recipe_preparation=ConfirmRecipePreparation(
            recipes, stock, consumer, transactions, memberships
        ),
        reassign_recipe_ingredient=reassign_recipe_ingredient,
        stock=stock,
        resolver=resolver,
        memberships=memberships,
        source_settings=source_settings,
    )
