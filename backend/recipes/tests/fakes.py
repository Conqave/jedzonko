from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager

from recipes.application.commands import RecipeInput, ResolvedIngredient
from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipeDetail, ExternalRecipePage
from recipes.domain.models import RecipeDetail, RecipeRequirement, RecipeSummary
from recipes.domain.stock import StockedProduct
from shared.household_membership import HouseholdMembershipReader
from shared.measurement import Quantity
from shared.transactions import TransactionManager


class FakeHouseholdMembershipReader(HouseholdMembershipReader):
    def __init__(self, member_household_ids: set[int]) -> None:
        self._member_household_ids = member_household_ids

    def is_member(self, user_id: int, household_id: int) -> bool:
        return household_id in self._member_household_ids


class FakeStockReader(HouseholdStockReader):
    def __init__(self, stock: list[StockedProduct]) -> None:
        self._stock = stock

    def get_stock(self, user_id: int, household_id: int) -> list[StockedProduct]:
        return self._stock


class FakeIngredientResolver(IngredientResolver):
    def __init__(self, ingredient_ids: dict[str, int]) -> None:
        self._ingredient_ids = ingredient_ids

    def find_ingredient_ids(self, names: tuple[str, ...]) -> dict[str, int]:
        return {name: self._ingredient_ids[name] for name in names if name in self._ingredient_ids}


class FakeRecipeRepository(RecipeRepository):
    def __init__(
        self,
        recipes: list[RecipeDetail],
        requirements: dict[int, list[RecipeRequirement]],
    ) -> None:
        self._recipes = recipes
        self._requirements = requirements
        self.requirement_query_count = 0

    def list_recipes(self) -> list[RecipeSummary]:
        return [recipe.summary for recipe in self._recipes]

    def find_recipe(self, recipe_id: int) -> RecipeDetail | None:
        for recipe in self._recipes:
            if recipe.summary.id == recipe_id:
                return recipe
        return None

    def list_requirements(self, recipe_id: int) -> list[RecipeRequirement]:
        self.requirement_query_count += 1
        return self._requirements.get(recipe_id, [])

    def list_requirements_by_recipe(self) -> dict[int, list[RecipeRequirement]]:
        self.requirement_query_count += 1
        return self._requirements

    def create_recipe(
        self,
        command: RecipeInput,
        ingredients: tuple[ResolvedIngredient, ...],
        created_by_user_id: int,
    ) -> RecipeDetail:
        raise AssertionError("Not used by these tests.")

    def update_recipe(
        self, recipe_id: int, command: RecipeInput, ingredients: tuple[ResolvedIngredient, ...]
    ) -> RecipeDetail:
        raise AssertionError("Not used by these tests.")

    def delete_recipe(self, recipe_id: int) -> None:
        raise AssertionError("Not used by these tests.")

    def reassign_ingredient(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        raise AssertionError("Not used by these tests.")


class FakeTransactionManager(TransactionManager):
    def __init__(self) -> None:
        self.entered_count = 0

    def atomic(self) -> AbstractContextManager[None]:
        return self._atomic()

    @contextmanager
    def _atomic(self) -> Iterator[None]:
        self.entered_count += 1
        yield


class FakeInventoryConsumer(HouseholdInventoryConsumer):
    def __init__(self) -> None:
        self.consumed: list[tuple[int, int, Quantity]] = []

    def consume(self, household_id: int, product_id: int, quantity: Quantity) -> None:
        self.consumed.append((household_id, product_id, quantity))


class FakeRecipeSource(RecipeSource):
    def __init__(self, page: ExternalRecipePage) -> None:
        self._page = page
        self.search_calls: list[tuple[str, tuple[str, ...], tuple[str, ...], int, int]] = []

    def get_recipe(self, reference: str) -> ExternalRecipeDetail:
        raise AssertionError("Not used by these tests.")

    def search_recipes(
        self,
        query: str,
        ingredient_names: tuple[str, ...],
        excluded_ingredient_names: tuple[str, ...],
        page: int,
        page_size: int,
    ) -> ExternalRecipePage:
        call = (query, ingredient_names, excluded_ingredient_names, page, page_size)
        self.search_calls.append(call)
        return self._page
