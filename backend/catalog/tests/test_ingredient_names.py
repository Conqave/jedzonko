import pytest

from catalog.domain.errors import InvalidIngredientNameError
from catalog.domain.names import MAX_INGREDIENT_NAME_LENGTH, IngredientNameText


@pytest.mark.parametrize(
    ("raw", "name", "normalized"),
    [
        ("Jajka", "Jajka", "jajka"),
        ("  Mąka   pszenna ", "Mąka pszenna", "maka pszenna"),
        ("ŁOSOŚ wędzony", "ŁOSOŚ wędzony", "losos wedzony"),
        ("Żółtko\tjaja", "Żółtko jaja", "zoltko jaja"),
    ],
)
def test_parsing_collapses_whitespace_and_normalizes(raw: str, name: str, normalized: str) -> None:
    text = IngredientNameText.parse(raw)

    assert text == IngredientNameText(name=name, normalized_name=normalized)


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_empty_names_are_rejected(raw: str) -> None:
    with pytest.raises(InvalidIngredientNameError):
        IngredientNameText.parse(raw)


def test_names_longer_than_the_column_are_rejected() -> None:
    IngredientNameText.parse("a" * MAX_INGREDIENT_NAME_LENGTH)

    with pytest.raises(InvalidIngredientNameError):
        IngredientNameText.parse("a" * (MAX_INGREDIENT_NAME_LENGTH + 1))


def test_the_normalized_form_is_bounded_too() -> None:
    # casefold turns "ß" into "ss", so the normalized form can outgrow the original.
    with pytest.raises(InvalidIngredientNameError):
        IngredientNameText.parse("ß" * MAX_INGREDIENT_NAME_LENGTH)
