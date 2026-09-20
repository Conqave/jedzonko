from decimal import Decimal

from inventory.domain.models import InventoryItemSnapshot
from recipes.domain.external import ExternalRecipePage, ExternalRecipeSummary
from recipes.domain.matching import (
    find_available_quantity,
    find_matched_product_names,
    find_matching_item,
    match_external_recipes,
    matches_product,
)
from recipes.domain.missing_items import calculate_shortfall
from recipes.tests.factories import (
    GRAM,
    KILOGRAM,
    MILLILITRE,
    PACKAGE,
    PIECE,
    make_requirement,
    make_snapshot,
)


def _eggs_in_a_package() -> InventoryItemSnapshot:
    return make_snapshot(
        1,
        "Jaja ściółkowe (opakowanie)",
        "1",
        PACKAGE,
        alias_names=("jajko", "jajka", "jaja"),
        package_quantity="10",
        package_unit=PIECE,
    )


def test_every_requirement_word_must_appear_in_the_product_name() -> None:
    product = make_snapshot(1, "Mąka pszenna typ 500", "1", KILOGRAM)

    assert matches_product("maka pszenna", product) is True
    assert matches_product("maka", product) is True


def test_a_requirement_word_is_never_matched_as_a_substring() -> None:
    assert matches_product("ser", make_snapshot(1, "Deser", "1", GRAM)) is False


def test_a_two_word_requirement_needs_both_words() -> None:
    product = make_snapshot(1, "Mąka ziemniaczana", "1", KILOGRAM)

    assert matches_product("maka pszenna", product) is False


def test_an_alias_matches_the_requirement_name_exactly() -> None:
    with_alias = make_snapshot(1, "Jaja ściółkowe", "1", PIECE, alias_names=("jajko",))
    without_alias = make_snapshot(2, "Jaja ściółkowe", "1", PIECE)

    assert matches_product("jajko", with_alias) is True
    assert matches_product("jajko", without_alias) is False


def test_the_alias_holder_wins_over_a_word_match() -> None:
    by_words = make_snapshot(1, "Mleko kozie", "1", MILLILITRE)
    by_alias = make_snapshot(2, "Napój roślinny", "1", MILLILITRE, alias_names=("mleko",))

    chosen = find_matching_item("mleko", [by_words, by_alias])

    assert chosen is not None
    assert chosen.id == 2


def test_the_shortest_product_name_wins_between_two_word_matches() -> None:
    chosen = find_matching_item(
        "maka",
        [
            make_snapshot(1, "Mąka pszenna typ 500", "1", KILOGRAM),
            make_snapshot(2, "Mąka", "1", KILOGRAM),
        ],
    )

    assert chosen is not None
    assert chosen.id == 2


def test_no_product_matches_an_unrelated_requirement() -> None:
    assert find_matching_item("kakao", [make_snapshot(1, "Mąka", "1", KILOGRAM)]) is None


def test_package_content_expresses_a_package_in_pieces() -> None:
    available = find_available_quantity(_eggs_in_a_package(), PIECE)

    assert available is not None
    assert available.amount == Decimal("10")
    assert available.unit == PIECE


def test_a_package_without_content_is_not_comparable_with_pieces() -> None:
    product = make_snapshot(1, "Jaja ściółkowe (opakowanie)", "1", PACKAGE)

    assert find_available_quantity(product, PIECE) is None


def test_no_conversion_is_invented_across_dimensions() -> None:
    product = make_snapshot(1, "Mleko", "1", KILOGRAM)

    assert find_available_quantity(product, MILLILITRE) is None


def test_a_package_of_eggs_satisfies_a_requirement_in_pieces() -> None:
    shortfall = calculate_shortfall([make_requirement("Jajko", "3", PIECE)], [_eggs_in_a_package()])

    assert shortfall.missing_items == ()
    assert shortfall.available_item_count == 1
    assert shortfall.is_ready is True


def test_the_same_product_without_package_content_stays_incomparable() -> None:
    product = make_snapshot(1, "Jaja ściółkowe (opakowanie)", "1", PACKAGE, alias_names=("jajko",))

    shortfall = calculate_shortfall([make_requirement("Jajko", "3", PIECE)], [product])

    assert shortfall.unmeasured_ingredient_names == ("Jajko",)
    assert shortfall.is_ready is False


def test_readiness_follows_the_pantry() -> None:
    requirements = [
        make_requirement("Jajko", "3", PIECE),
        make_requirement("Mąka pszenna", "500", GRAM),
    ]
    flour = make_snapshot(2, "Mąka pszenna typ 500", "1", KILOGRAM)

    assert calculate_shortfall(requirements, [_eggs_in_a_package(), flour]).is_ready is True
    assert calculate_shortfall(requirements, [_eggs_in_a_package()]).is_ready is False


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


def test_matched_pantry_products_come_from_the_provider_tags() -> None:
    inventory = [_eggs_in_a_package(), make_snapshot(2, "Mąka pszenna typ 500", "1", KILOGRAM)]

    matched = find_matched_product_names(("dla dzieci", "jajko", "mąka pszenna"), inventory)

    assert matched == ("Jaja ściółkowe (opakowanie)", "Mąka pszenna typ 500")


def test_recipes_matching_more_of_the_pantry_come_first() -> None:
    inventory = [_eggs_in_a_package(), make_snapshot(2, "Mąka pszenna typ 500", "1", KILOGRAM)]
    page = ExternalRecipePage(
        recipes=(
            _summary("zupa", "Zupa", ("woda", "sól")),
            _summary("nalesniki", "Naleśniki", ("jajko", "mąka pszenna", "dla dzieci")),
            _summary("omlet", "Omlet", ("jajko",)),
        ),
        page=0,
        page_size=12,
        total_count=3,
        total_pages=1,
    )

    matched = match_external_recipes(page, inventory)

    assert [item.summary.reference for item in matched.matches] == ["nalesniki", "omlet", "zupa"]
    assert matched.matches[0].matched_product_names == (
        "Jaja ściółkowe (opakowanie)",
        "Mąka pszenna typ 500",
    )
    assert matched.matches[2].matched_product_names == ()
    assert matched.total_count == 3
