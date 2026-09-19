import pytest

from households.application.access import HouseholdAccessPolicy
from households.application.errors import NotAHouseholdMemberError
from inventory.domain.models import InventoryItemSnapshot
from recipes.application.use_cases.suggest_recipes_from_inventory import SuggestRecipesFromInventory
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.tests.factories import GRAM, MILLILITRE, make_requirement, make_snapshot
from recipes.tests.fakes import (
    FakeHouseholdInventoryReader,
    FakeHouseholdRepository,
    FakeRecipeRepository,
)


def _recipe(recipe_id: int, name: str) -> RecipeDetail:
    summary = RecipeSummary(
        id=recipe_id,
        name=name,
        description="",
        servings=2,
        preparation_time_minutes=10,
        cooking_time_minutes=20,
        difficulty=RecipeDifficulty.EASY,
        category_name=None,
        tag_names=(),
        image_url=None,
        author_username="ala",
    )
    return RecipeDetail(summary=summary, steps=(), ingredients=())


def _build(
    repository: FakeRecipeRepository, inventory: list[InventoryItemSnapshot]
) -> SuggestRecipesFromInventory:
    return SuggestRecipesFromInventory(
        repository,
        FakeHouseholdInventoryReader(inventory),
        HouseholdAccessPolicy(FakeHouseholdRepository({7})),
    )


def test_recipe_fully_in_stock_has_no_missing_items() -> None:
    repository = FakeRecipeRepository(
        [_recipe(1, "omlet")], {1: [make_requirement("jajko", "2", GRAM)]}
    )
    use_case = _build(repository, [make_snapshot(1, "jajko", "10", GRAM)])

    suggestions = use_case.execute(5, 7)

    assert suggestions[0].shortfall.missing_items == ()
    assert suggestions[0].shortfall.available_item_count == 1
    assert suggestions[0].shortfall.is_ready is True


def test_suggestions_are_ordered_and_read_requirements_once() -> None:
    repository = FakeRecipeRepository(
        [_recipe(1, "zupa"), _recipe(2, "bigos")],
        {
            1: [make_requirement("jajko", "2", GRAM), make_requirement("mleko", "1", GRAM)],
            2: [make_requirement("jajko", "2", GRAM)],
        },
    )
    use_case = _build(repository, [make_snapshot(1, "jajko", "10", GRAM)])

    suggestions = use_case.execute(5, 7)

    assert [item.recipe_id for item in suggestions] == [2, 1]
    assert repository.requirement_query_count == 1


def test_incompatible_unit_counts_as_missing() -> None:
    repository = FakeRecipeRepository(
        [_recipe(1, "nalesniki")], {1: [make_requirement("mleko", "250", MILLILITRE)]}
    )
    use_case = _build(repository, [make_snapshot(1, "mleko", "900", GRAM)])

    suggestions = use_case.execute(5, 7)

    assert len(suggestions[0].shortfall.missing_items) == 1
    assert suggestions[0].shortfall.missing_items[0].unit_code == "ml"
    assert suggestions[0].shortfall.unmeasured_ingredient_names == ("mleko",)
    assert suggestions[0].shortfall.is_ready is False


def test_non_member_is_rejected() -> None:
    repository = FakeRecipeRepository([], {})
    use_case = _build(repository, [])

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(5, 99)
