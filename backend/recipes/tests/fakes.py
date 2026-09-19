from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

from households.application.ports.household_repository import HouseholdRepository
from households.domain.models import HouseholdMember, HouseholdSummary
from inventory.domain.models import InventoryItemSnapshot
from recipes.application.commands import RecipeInput
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.application.ports.transaction_manager import TransactionManager
from recipes.domain.models import RecipeDetail, RecipeRequirement, RecipeSummary


class FakeHouseholdRepository(HouseholdRepository):
    def __init__(self, member_household_ids: set[int]) -> None:
        self._member_household_ids = member_household_ids

    def find_households_for_user(self, user_id: int) -> list[HouseholdSummary]:
        raise NotImplementedError

    def find_household(self, household_id: int) -> HouseholdSummary | None:
        raise NotImplementedError

    def is_member(self, user_id: int, household_id: int) -> bool:
        return household_id in self._member_household_ids

    def list_members(self, household_id: int) -> list[HouseholdMember]:
        raise NotImplementedError

    def create_household(self, name: str, owner_user_id: int) -> HouseholdSummary:
        raise NotImplementedError

    def add_member(self, household_id: int, username: str) -> HouseholdMember:
        raise NotImplementedError

    def remove_member(self, household_id: int, user_id: int) -> None:
        raise NotImplementedError

    def count_members(self, household_id: int) -> int:
        raise NotImplementedError


class FakeHouseholdInventoryReader(HouseholdInventoryReader):
    def __init__(self, items: list[InventoryItemSnapshot]) -> None:
        self._items = items

    def read_inventory(self, user_id: int, household_id: int) -> list[InventoryItemSnapshot]:
        return self._items


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

    def create_recipe(self, command: RecipeInput, created_by_user_id: int) -> RecipeDetail:
        raise NotImplementedError

    def update_recipe(self, recipe_id: int, command: RecipeInput) -> RecipeDetail:
        raise NotImplementedError

    def delete_recipe(self, recipe_id: int) -> None:
        raise NotImplementedError


class FakeTransactionManager(TransactionManager):
    def __init__(self) -> None:
        self.entered_count = 0

    @contextmanager
    def atomic(self) -> Iterator[None]:
        self.entered_count += 1
        yield


class FakeHouseholdInventoryConsumer(HouseholdInventoryConsumer):
    def __init__(self) -> None:
        self.consumed: list[tuple[int, int, Decimal, str]] = []

    def consume(self, household_id: int, product_id: int, amount: Decimal, unit_code: str) -> None:
        self.consumed.append((household_id, product_id, amount, unit_code))
