from recipes.domain.ranking import rank_suggestions
from recipes.domain.suggestion import MissingRecipeItem, RecipeShortfall, RecipeSuggestion
from recipes.tests.factories import make_missing_item


def _suggestion(recipe_id: int, name: str, available: int, missing: int) -> RecipeSuggestion:
    missing_items: tuple[MissingRecipeItem, ...] = tuple(
        make_missing_item(f"brak {index}") for index in range(missing)
    )
    return RecipeSuggestion(
        recipe_id=recipe_id,
        recipe_name=name,
        shortfall=RecipeShortfall(
            missing_items=missing_items,
            unmeasured_ingredient_names=(),
            required_item_count=available + missing,
            available_item_count=available,
        ),
    )


def test_fewest_missing_items_come_first() -> None:
    ranked = rank_suggestions([_suggestion(1, "a", 1, 2), _suggestion(2, "b", 1, 0)])

    assert [item.recipe_id for item in ranked] == [2, 1]


def test_more_available_items_break_the_tie() -> None:
    ranked = rank_suggestions([_suggestion(1, "a", 1, 1), _suggestion(2, "b", 4, 1)])

    assert [item.recipe_id for item in ranked] == [2, 1]


def test_name_breaks_remaining_ties() -> None:
    ranked = rank_suggestions([_suggestion(1, "zupa", 2, 1), _suggestion(2, "bigos", 2, 1)])

    assert [item.recipe_name for item in ranked] == ["bigos", "zupa"]
