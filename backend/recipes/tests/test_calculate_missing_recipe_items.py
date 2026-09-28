from decimal import Decimal

import pytest

from recipes.application.errors import InvalidServingsError, RecipeNotFoundError
from recipes.application.use_cases.calculate_missing_recipe_items import CalculateMissingRecipeItems
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.domain.stock import StockedProduct
from recipes.tests.factories import EGGS, GRAM, make_requirement, make_stock
from recipes.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeRecipeRepository,
    FakeStockReader,
)
from shared.household_membership import NotAHouseholdMemberError


def _recipe(servings: int) -> RecipeDetail:
    summary = RecipeSummary(
        id=1,
        name="omlet",
        description="",
        servings=servings,
        preparation_time_minutes=5,
        cooking_time_minutes=5,
        difficulty=RecipeDifficulty.EASY,
        category_name=None,
        tag_names=(),
        image_url=None,
        author_username="ala",
    )
    return RecipeDetail(summary=summary, steps=(), ingredients=())


def _build(
    repository: FakeRecipeRepository, inventory: list[StockedProduct]
) -> CalculateMissingRecipeItems:
    return CalculateMissingRecipeItems(
        repository,
        FakeStockReader(inventory),
        FakeHouseholdMembershipReader({7}),
    )


def test_missing_amount_follows_requested_servings() -> None:
    repository = FakeRecipeRepository(
        [_recipe(2)], {1: [make_requirement("jajko", "2", GRAM, EGGS)]}
    )
    use_case = _build(repository, [make_stock(1, "jajko", "3", GRAM, EGGS)])

    shortfall = use_case.execute(5, 7, 1, 4)

    assert shortfall.missing_items[0].amount == Decimal("1")
    assert shortfall.missing_items[0].unit_code == "g"
    assert shortfall.is_ready is False


def test_non_member_is_rejected() -> None:
    use_case = _build(FakeRecipeRepository([_recipe(2)], {}), [])

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(5, 99, 1, 2)


def test_zero_servings_is_rejected() -> None:
    use_case = _build(FakeRecipeRepository([_recipe(2)], {}), [])

    with pytest.raises(InvalidServingsError):
        use_case.execute(5, 7, 1, 0)


def test_unknown_recipe_is_rejected() -> None:
    use_case = _build(FakeRecipeRepository([], {}), [])

    with pytest.raises(RecipeNotFoundError):
        use_case.execute(5, 7, 404, 2)
