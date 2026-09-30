import pytest

from recipes.domain.servings import read_servings


@pytest.mark.parametrize(
    ("yield_label", "servings"),
    [
        ("6 porcji", 6),
        ("1 porcja", 1),
        ("dla 4 osób", 4),
        ("Dla 2 osoby", 2),
        ("12 sztuk", 12),
        ("24 szt.", 24),
        ("około 1200 g - 4 małe porcje", 4),
        ("8 dużych porcji po 250 g", 8),
    ],
)
def test_a_stated_count_of_portions_or_pieces_gives_the_servings(
    yield_label: str, servings: int
) -> None:
    assert read_servings(yield_label) == servings


@pytest.mark.parametrize(
    "yield_label",
    [
        None,
        "",
        "2300 gramów sernika",
        "forma 24 x 24 cm",
        "do 16 naleśników średnicy 24 cm",
        "minimum 12 dużych knedli",
        "gruby omlet o średnicy 18 cm ",
        "4-6 porcji",
        "4 \N{EN DASH} 6 osób",
        "6\N{EM DASH}8 porcji",
        "0 porcji",
        "1,5 porcji",
        "6 porcjowanych kawałków",
    ],
)
def test_a_label_without_a_definite_count_gives_no_servings(yield_label: str | None) -> None:
    assert read_servings(yield_label) is None
