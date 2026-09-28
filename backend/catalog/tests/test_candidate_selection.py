from catalog.domain.candidate_selection import select_classification_candidates
from catalog.domain.ingredient import IngredientName, IngredientNameKind, IngredientNameSource


def _name(ingredient_id: int, normalized_name: str) -> IngredientName:
    return IngredientName(
        ingredient_id=ingredient_id,
        name=normalized_name,
        normalized_name=normalized_name,
        kind=IngredientNameKind.CANONICAL,
        source=IngredientNameSource.ANIA_GOTUJE,
    )


def test_ingredients_sharing_more_words_come_first() -> None:
    names = [_name(1, "cebula"), _name(2, "cebula czerwona"), _name(3, "papryka czerwona")]

    ranked = select_classification_candidates("cebula czerwona duza", names)

    assert ranked == [2, 1, 3]


def test_an_ingredient_counts_once_through_its_best_name() -> None:
    names = [_name(1, "jajka"), _name(1, "jajka wiejskie"), _name(2, "mleko")]

    ranked = select_classification_candidates("jajka wiejskie", names)

    assert ranked == [1]
