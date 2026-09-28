from decimal import Decimal

from recipes.domain.external import ExternalRecipePage, ExternalRecipeSummary
from recipes.domain.matching import (
    available_quantity,
    consumption_in_stock_unit,
    find_stock,
    match_external_recipes,
)
from recipes.domain.missing_items import calculate_shortfall
from recipes.domain.stock import StockedProduct
from recipes.tests.factories import (
    EGGS,
    FLOUR,
    GRAM,
    KILOGRAM,
    MILLILITRE,
    PACKAGE,
    PIECE,
    make_requirement,
    make_stock,
)
from shared.measurement import Quantity


def _eggs_in_packages(packages: str = "1") -> StockedProduct:
    ten_pieces = Quantity(amount=Decimal("10"), unit=PIECE)
    return make_stock(1, "Jaja ściółkowe (opakowanie)", packages, PACKAGE, EGGS, ten_pieces)


def test_a_requirement_matches_only_products_confirmed_as_its_ingredient() -> None:
    flour = make_stock(1, "Mąka pszenna typ 500", "1", KILOGRAM, FLOUR)
    unclassified = make_stock(2, "Mąka pszenna", "1", KILOGRAM, None)

    match = find_stock(FLOUR, GRAM, [unclassified, flour])

    assert match is not None and match.product.product_id == 1


def test_an_unresolved_requirement_matches_nothing() -> None:
    flour = make_stock(1, "Mąka pszenna", "1", KILOGRAM, FLOUR)

    assert find_stock(None, GRAM, [flour]) is None


def test_the_product_with_most_comparable_stock_covers_the_requirement() -> None:
    small = make_stock(1, "Mąka tortowa", "200", GRAM, FLOUR)
    large = make_stock(2, "Mąka typ 500", "1", KILOGRAM, FLOUR)

    match = find_stock(FLOUR, GRAM, [small, large])

    assert match is not None
    assert match.product.product_id == 2
    assert match.available == Quantity(amount=Decimal("1000"), unit=GRAM)


def test_a_product_that_cannot_be_measured_is_reported_without_an_amount() -> None:
    no_content = make_stock(1, "Jaja", "1", PACKAGE, EGGS)

    match = find_stock(EGGS, PIECE, [no_content])

    assert match is not None and match.available is None


def test_package_content_expresses_packages_in_pieces() -> None:
    available = available_quantity(_eggs_in_packages("2"), PIECE)

    assert available == Quantity(amount=Decimal("20"), unit=PIECE)


def test_no_conversion_is_invented_across_dimensions() -> None:
    flour = make_stock(1, "Mąka", "1", KILOGRAM, FLOUR)

    assert available_quantity(flour, MILLILITRE) is None


def test_a_requirement_is_consumed_in_the_products_own_unit() -> None:
    three_pieces = Quantity(amount=Decimal("5"), unit=PIECE)

    used = consumption_in_stock_unit(_eggs_in_packages(), three_pieces)

    assert used == Quantity(amount=Decimal("0.5"), unit=PACKAGE)


def test_consumption_is_not_invented_without_package_content() -> None:
    no_content = make_stock(1, "Jaja", "1", PACKAGE, EGGS)
    three_pieces = Quantity(amount=Decimal("3"), unit=PIECE)

    assert consumption_in_stock_unit(no_content, three_pieces) is None


def test_readiness_follows_the_pantry() -> None:
    requirements = [
        make_requirement("Jajko", "3", PIECE, EGGS),
        make_requirement("Mąka pszenna", "500", GRAM, FLOUR),
    ]
    flour = make_stock(2, "Mąka pszenna typ 500", "1", KILOGRAM, FLOUR)

    with_flour = calculate_shortfall(requirements, [_eggs_in_packages(), flour])
    without_flour = calculate_shortfall(requirements, [_eggs_in_packages()])

    assert with_flour.is_ready is True
    assert without_flour.is_ready is False


def _summary(reference: str, name: str, tag_names: tuple[str, ...]) -> ExternalRecipeSummary:
    return ExternalRecipeSummary(
        source_name="Ania Gotuje",
        source_url=f"https://aniagotuje.pl/przepis/{reference}",
        reference=reference,
        name=name,
        description="",
        image_url=None,
        yield_label="",
        total_time_minutes=None,
        tag_names=tag_names,
    )


def test_external_recipes_matching_more_of_the_pantry_come_first() -> None:
    stock = [_eggs_in_packages(), make_stock(2, "Mąka pszenna typ 500", "1", KILOGRAM, FLOUR)]
    page = ExternalRecipePage(
        recipes=(
            _summary("zupa", "Zupa", ("woda", "sól")),
            _summary("nalesniki", "Naleśniki", ("jajka", "mąka pszenna", "dla dzieci")),
            _summary("omlet", "Omlet", ("jajka",)),
        ),
        page=0,
        page_size=12,
        total_count=3,
        total_pages=1,
    )
    resolved = {"jajka": EGGS, "mąka pszenna": FLOUR}

    matched = match_external_recipes(page, stock, resolved)

    assert [item.summary.reference for item in matched.matches] == ["nalesniki", "omlet", "zupa"]
    assert matched.matches[0].matched_product_names == (
        "Jaja ściółkowe (opakowanie)",
        "Mąka pszenna typ 500",
    )
    assert matched.matches[2].matched_product_names == ()
    assert matched.total_count == 3
