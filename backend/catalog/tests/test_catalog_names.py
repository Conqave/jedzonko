import pytest

from catalog.domain.errors import InvalidNameError
from catalog.domain.names import MAX_NAME_LENGTH, CatalogName


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
    text = CatalogName.parse(raw)

    assert text == CatalogName(name=name, normalized_name=normalized)


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_empty_names_are_rejected(raw: str) -> None:
    with pytest.raises(InvalidNameError):
        CatalogName.parse(raw)


def test_names_longer_than_the_column_are_rejected() -> None:
    CatalogName.parse("a" * MAX_NAME_LENGTH)

    with pytest.raises(InvalidNameError):
        CatalogName.parse("a" * (MAX_NAME_LENGTH + 1))


def test_the_normalized_form_is_bounded_too() -> None:
    with pytest.raises(InvalidNameError):
        CatalogName.parse("ß" * MAX_NAME_LENGTH)
