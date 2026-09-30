import pytest

from recipes.application.use_cases.suggest_external_recipes_from_inventory import (
    SuggestExternalRecipesFromInventory,
)
from recipes.domain.external import ExternalRecipePage, ExternalRecipeSummary
from recipes.tests.factories import EGGS, GRAM, MILK, SUGAR, make_stock
from recipes.tests.fakes import (
    FakeExternalRecipeCatalog,
    FakeHouseholdMembershipReader,
    FakeIngredientResolver,
    FakeRecipeSource,
    FakeStockReader,
)
from shared.household_membership import NotAHouseholdMemberError


def _page() -> ExternalRecipePage:
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
    return ExternalRecipePage(
        recipes=(summary,), page=0, page_size=12, total_count=1, total_pages=1
    )


def test_pantry_selection_is_bounded_and_echoed_back() -> None:
    source = FakeRecipeSource(_page(), {})
    use_case = SuggestExternalRecipesFromInventory(
        FakeExternalRecipeCatalog(),
        source,
        FakeStockReader(
            [
                make_stock(1, "mleko", "1", GRAM, MILK),
                make_stock(2, "jajko", "3", GRAM, EGGS),
                make_stock(3, "cukier", "1", GRAM, SUGAR),
            ]
        ),
        FakeIngredientResolver({"jajko": EGGS}),
        FakeHouseholdMembershipReader({7}),
        2,
    )

    suggestions = use_case.execute(5, 7, 0, 12)

    assert suggestions.ingredient_names == ("cukier", "jajko")
    assert suggestions.inventory_item_count == 3
    assert source.search_calls == [
        ("", ("cukier",), (), 0, 12),
        ("", ("jajko",), (), 0, 12),
    ]
    assert suggestions.page.total_count == 1
    assert suggestions.page.matches[0].matched_product_names == ("jajko",)


def test_empty_pantry_does_not_call_the_provider() -> None:
    source = FakeRecipeSource(_page(), {})
    use_case = SuggestExternalRecipesFromInventory(
        FakeExternalRecipeCatalog(),
        source,
        FakeStockReader([]),
        FakeIngredientResolver({"jajko": EGGS}),
        FakeHouseholdMembershipReader({7}),
        2,
    )

    suggestions = use_case.execute(5, 7, 0, 12)

    assert source.search_calls == []
    assert suggestions.page.matches == ()
    assert suggestions.ingredient_names == ()
    assert suggestions.inventory_item_count == 0


def test_non_member_is_rejected() -> None:
    use_case = SuggestExternalRecipesFromInventory(
        FakeExternalRecipeCatalog(),
        FakeRecipeSource(_page(), {}),
        FakeStockReader([]),
        FakeIngredientResolver({"jajko": EGGS}),
        FakeHouseholdMembershipReader({7}),
        2,
    )

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(5, 99, 0, 12)


def test_ingredient_limit_must_be_positive() -> None:
    with pytest.raises(ValueError):
        SuggestExternalRecipesFromInventory(
            FakeExternalRecipeCatalog(),
            FakeRecipeSource(_page(), {}),
            FakeStockReader([]),
            FakeIngredientResolver({}),
            FakeHouseholdMembershipReader({7}),
            0,
        )
