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
from recipes.domain.external_line import LineInterpretation
from recipes.tests.factories import EGGS, GRAM, MILK, make_stock
from recipes.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeIngredientLineRepository,
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


def _use_case(
    member_household_ids: set[int],
    interpretations: dict[str, LineInterpretation] | None = None,
) -> CalculateExternalRecipeShortfall:
    lines = FakeIngredientLineRepository({} if interpretations is None else interpretations)
    return CalculateExternalRecipeShortfall(
        FakeRecipeSource(EMPTY_PAGE, {"omlet": _omelette()}),
        FakeStockReader([make_stock(1, "jajka", "10", GRAM, EGGS)]),
        FakeIngredientResolver({"jajko": EGGS, "mleko": MILK}),
        lines,
        FakeHouseholdMembershipReader(member_household_ids),
    )


def test_shortfall_lists_what_the_pantry_lacks() -> None:
    shortfall = _use_case({HOME}).execute(ALA, HOME, "omlet")

    missing = [(item.name, item.amount, item.unit_code) for item in shortfall.missing_items]
    assert missing == [("mleko", Decimal("200"), "g"), ("sól", None, None)]
    assert shortfall.is_ready is False


def test_a_stored_interpretation_names_the_ingredient_and_amount_of_a_line() -> None:
    salt = LineInterpretation(ingredient_id=MILK, quantity=Decimal("5"), unit_code="g")

    shortfall = _use_case({HOME}, {"sol do smaku": salt}).execute(ALA, HOME, "omlet")

    missing = [(item.name, item.ingredient_id, item.amount) for item in shortfall.missing_items]
    assert ("sól", MILK, Decimal("5")) in missing


def test_an_amount_parsed_from_the_line_wins_over_the_interpretation() -> None:
    milk = LineInterpretation(ingredient_id=MILK, quantity=Decimal("999"), unit_code="g")

    shortfall = _use_case({HOME}, {"200 g mleka": milk}).execute(ALA, HOME, "omlet")

    milk_item = next(item for item in shortfall.missing_items if item.name == "mleko")
    assert milk_item.amount == Decimal("200")


def test_an_unknown_recipe_is_reported_by_the_source() -> None:
    with pytest.raises(RecipeNotFoundAtSourceError):
        _use_case({HOME}).execute(ALA, HOME, "nieznany")


def test_a_non_member_is_rejected() -> None:
    with pytest.raises(NotAHouseholdMemberError):
        _use_case(set()).execute(ALA, HOME, "omlet")
