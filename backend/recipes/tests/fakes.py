from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime

from recipes.application.commands import RecipeInput, ResolvedIngredient
from recipes.application.errors import RecipeNotFoundAtSourceError, RecipeSourceError
from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.application.ports.recipe_site import RecipeSite
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import (
    ExternalRecipeDetail,
    ExternalRecipeIngredient,
    ExternalRecipePage,
    ImportedExternalRecipe,
    RecipeImage,
)
from recipes.domain.external_line import LineInterpretation
from recipes.domain.models import RecipeCategory, RecipeDetail, RecipeRequirement, RecipeSummary
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
        self.tagged: list[tuple[str, int]] = []

    def list_recipes(self) -> list[RecipeSummary]:
        return [recipe.summary for recipe in self._recipes]

    def list_categories(self) -> list[RecipeCategory]:
        return []

    def list_untagged_ingredient_names(self) -> tuple[str, ...]:
        names = {
            line.name
            for recipe in self._recipes
            for line in recipe.ingredients
            if line.ingredient_id is None
        }
        return tuple(sorted(names))

    def tag_ingredient_lines(self, name: str, ingredient_id: int) -> int:
        self.tagged.append((name, ingredient_id))
        return 1

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
    def __init__(self, page: ExternalRecipePage, recipes: dict[str, ExternalRecipeDetail]) -> None:
        self._page = page
        self._recipes = recipes
        self.search_calls: list[tuple[str, tuple[str, ...], tuple[str, ...], int, int]] = []

    def get_recipe(self, reference: str) -> ExternalRecipeDetail:
        recipe = self._recipes.get(reference)
        if recipe is None:
            raise RecipeNotFoundAtSourceError
        return recipe

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


class FakeIngredientLines(IngredientLines):
    def __init__(self, interpretations: dict[str, LineInterpretation]) -> None:
        self.interpretations = interpretations
        self.interpreted: list[tuple[str, ...]] = []

    def find_interpretations(self, texts: tuple[str, ...]) -> dict[str, LineInterpretation]:
        return {text: self.interpretations[text] for text in texts if text in self.interpretations}

    def interpret(self, texts: tuple[str, ...], now: datetime) -> int:
        self.interpreted.append(texts)
        return len([text for text in texts if text not in self.interpretations])


class FakeExternalRecipeCatalog(ExternalRecipeCatalog):
    def __init__(self) -> None:
        self.recipes: dict[str, ImportedExternalRecipe] = {}
        self.images: dict[str, RecipeImage] = {}
        self.fetched_at: dict[str, datetime] = {}

    def list_references(self) -> frozenset[str]:
        return frozenset(self.recipes)

    def list_missing_images(self) -> dict[str, str]:
        return {
            reference: recipe.image_source_url
            for reference, recipe in self.recipes.items()
            if recipe.image_source_url is not None and reference not in self.images
        }

    def find_ingredients(self, reference: str) -> tuple[ExternalRecipeIngredient, ...] | None:
        recipe = self.recipes.get(reference)
        return None if recipe is None else recipe.ingredients

    def find_image_urls(self, references: tuple[str, ...]) -> dict[str, str]:
        return {
            reference: f"media/external_recipes/{self.images[reference].filename}"
            for reference in references
            if reference in self.images
        }

    def list_ingredient_texts(self) -> tuple[str, ...]:
        texts = {
            line.source_text for recipe in self.recipes.values() for line in recipe.ingredients
        }
        return tuple(sorted(texts))

    def save_recipe(
        self, recipe: ImportedExternalRecipe, image: RecipeImage | None, fetched_at: datetime
    ) -> None:
        self.recipes[recipe.reference] = recipe
        self.fetched_at[recipe.reference] = fetched_at
        if image is not None:
            self.images[recipe.reference] = image

    def save_image(self, reference: str, image: RecipeImage) -> None:
        self.images[reference] = image


class FakeRecipeSite(RecipeSite):
    def __init__(
        self,
        references: tuple[str, ...],
        pages: dict[str, ImportedExternalRecipe | RecipeSourceError],
        images: dict[str, RecipeImage | RecipeSourceError],
    ) -> None:
        self._references = references
        self._pages = pages
        self._images = images
        self.fetched: list[str] = []
        self.fetched_images: list[str] = []

    def list_recipe_references(self) -> tuple[str, ...]:
        return self._references

    def fetch_recipe(self, reference: str) -> ImportedExternalRecipe:
        self.fetched.append(reference)
        page = self._pages[reference]
        if isinstance(page, RecipeSourceError):
            raise page
        return page

    def fetch_image(self, reference: str, url: str) -> RecipeImage:
        self.fetched_images.append(url)
        image = self._images[url]
        if isinstance(image, RecipeSourceError):
            raise image
        return image
