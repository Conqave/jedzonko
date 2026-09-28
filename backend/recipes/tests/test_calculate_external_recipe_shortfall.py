from decimal import Decimal

import pytest

from recipes.application.errors import RecipeNotFoundAtSourceError
from recipes.application.use_cases.calculate_external_recipe_shortfall import (
    CalculateExternalRecipeShortfall,
)
from recipes.domain.external import (
    ExternalRecipeDetail,
    ExternalRecipeIngredient,
    ExternalRecipePage,
    ExternalRecipeSummary,
)
from recipes.tests.factories import EGGS, GRAM, MILK, make_stock
from recipes.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeIngredientResolver,
    FakeRecipeSource,
    FakeStockReader,
)
from shared.household_membership import NotAHouseholdMemberError

ALA = 5
HOME = 7
EMPTY_PAGE = ExternalRecipePage(recipes=(), page=0, page_size=12, total_count=0, total_pages=0)


def _omelette() -> ExternalRecipeDetail:
    summary = ExternalRecipeSummary(
        source_name="Ania Gotuje",
        source_url="https://aniagotuje.pl/przepis/omlet",
        reference="omlet",
        name="Omlet",
        description="",
        image_url=None,
        yield_label="",
        total_time_minutes=15,
        tag_names=("jajko",),
    )
    ingredients = (
        ExternalRecipeIngredient("3 jajka", "jajko", Decimal("3"), "g"),
        ExternalRecipeIngredient("200 g mleka", "mleko", Decimal("200"), "g"),
        ExternalRecipeIngredient("sól do smaku", "sól", None, None),
    )
    return ExternalRecipeDetail(
        summary=summary,
        preparation_time_minutes=5,
        cooking_time_minutes=10,
        steps=("Usmaż.",),
        ingredients=ingredients,
    )


def _use_case(member_household_ids: set[int]) -> CalculateExternalRecipeShortfall:
    return CalculateExternalRecipeShortfall(
        FakeRecipeSource(EMPTY_PAGE, {"omlet": _omelette()}),
        FakeStockReader([make_stock(1, "jajka", "10", GRAM, EGGS)]),
        FakeIngredientResolver({"jajko": EGGS, "mleko": MILK}),
        FakeHouseholdMembershipReader(member_household_ids),
    )


def test_shortfall_lists_what_the_pantry_lacks() -> None:
    shortfall = _use_case({HOME}).execute(ALA, HOME, "omlet")

    missing = [(item.name, item.amount, item.unit_code) for item in shortfall.missing_items]
    assert missing == [("mleko", Decimal("200"), "g"), ("sól", None, None)]
    assert shortfall.is_ready is False


def test_an_unknown_recipe_is_reported_by_the_source() -> None:
    with pytest.raises(RecipeNotFoundAtSourceError):
        _use_case({HOME}).execute(ALA, HOME, "nieznany")


def test_a_non_member_is_rejected() -> None:
    with pytest.raises(NotAHouseholdMemberError):
        _use_case(set()).execute(ALA, HOME, "omlet")
