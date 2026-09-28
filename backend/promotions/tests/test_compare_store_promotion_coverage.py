import pytest

from promotions.application.errors import InvalidPromotionQueryError
from promotions.application.shop_selection import ShopSelection
from promotions.application.use_cases.compare_store_promotion_coverage import (
    CompareStorePromotionCoverage,
)
from promotions.domain.models import FavouriteShop
from promotions.tests.fakes import FakeFavouriteShopRepository, FakePromotionSource, build_offer

USER_ID = 7


def _build_use_case(
    source: FakePromotionSource, favourites: list[FavouriteShop]
) -> CompareStorePromotionCoverage:
    repository = FakeFavouriteShopRepository({USER_ID: favourites})
    return CompareStorePromotionCoverage(source, ShopSelection(repository))


def _build_source() -> FakePromotionSource:
    return FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "hash-1"),
                build_offer("Twaróg", "Lidl", "hash-2"),
                build_offer("Twaróg", "Carrefour", "hash-3"),
            ],
            "masło": [
                build_offer("Masło", "Carrefour", "hash-4"),
                build_offer("Masło", "Lidl", "hash-5"),
            ],
        }
    )


def test_coverage_ranks_stores_by_number_of_matched_requested_items() -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "hash-1"),
                build_offer("Twaróg wiejski", "Lidl", "hash-2"),
            ],
            "masło": [build_offer("Masło extra", "Biedronka", "hash-3")],
        }
    )

    coverage = _build_use_case(source, []).execute(USER_ID, ["twaróg", "masło"], None)

    assert [(item.shop_name, item.shop_slug, item.matched_query_count) for item in coverage] == [
        ("Biedronka", "biedronka", 2),
        ("Lidl", "lidl", 1),
    ]
    assert coverage[0].matched_queries == ("twaróg", "masło")
    assert len(coverage[0].offers) == 2


def test_coverage_counts_each_requested_item_once_per_store() -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Lidl", "hash-1"),
                build_offer("Twaróg light", "Lidl", "hash-2"),
            ]
        }
    )

    coverage = _build_use_case(source, []).execute(USER_ID, ["twaróg"], None)

    assert coverage[0].matched_query_count == 1
    assert len(coverage[0].offers) == 2


def test_coverage_deduplicates_requested_items() -> None:
    source = FakePromotionSource({"twaróg": [build_offer("Twaróg", "Lidl", "hash-1")]})

    _build_use_case(source, []).execute(USER_ID, ["twaróg", " twaróg "], None)

    assert source.received_queries == ["twaróg"]


def test_coverage_ranks_only_the_explicitly_requested_shops() -> None:
    source = _build_source()

    coverage = _build_use_case(source, []).execute(
        USER_ID, ["twaróg", "masło"], ("lidl", "biedronka")
    )

    assert [(item.shop_slug, item.matched_query_count) for item in coverage] == [
        ("lidl", 2),
        ("biedronka", 1),
    ]


def test_coverage_uses_saved_favourites_when_no_shops_are_requested() -> None:
    source = _build_source()
    favourites = [
        FavouriteShop(name="Biedronka", slug="biedronka"),
        FavouriteShop(name="Lidl", slug="lidl"),
    ]

    coverage = _build_use_case(source, favourites).execute(USER_ID, ["twaróg", "masło"], None)

    assert [item.shop_slug for item in coverage] == ["lidl", "biedronka"]
    assert source.received_shop_slugs == [("biedronka", "lidl"), ("biedronka", "lidl")]


def test_coverage_prefers_explicit_shops_over_favourites() -> None:
    source = _build_source()
    favourites = [FavouriteShop(name="Lidl", slug="lidl")]

    coverage = _build_use_case(source, favourites).execute(
        USER_ID, ["twaróg", "masło"], ("carrefour",)
    )

    assert [item.shop_slug for item in coverage] == ["carrefour"]


def test_coverage_uses_all_shops_without_favourites_and_without_requested_shops() -> None:
    source = _build_source()

    coverage = _build_use_case(source, []).execute(USER_ID, ["twaróg", "masło"], None)

    assert [item.shop_slug for item in coverage] == ["carrefour", "lidl", "biedronka"]
    assert source.received_shop_slugs == [(), ()]


def test_coverage_ignores_unknown_shop_slugs() -> None:
    source = FakePromotionSource({"twaróg": [build_offer("Twaróg", "Lidl", "hash-1")]})

    assert _build_use_case(source, []).execute(USER_ID, ["twaróg"], ("biedornka",)) == []


def test_coverage_is_empty_when_no_store_has_matches() -> None:
    source = FakePromotionSource({})

    assert _build_use_case(source, []).execute(USER_ID, ["twaróg"], None) == []


def test_coverage_rejects_blank_requested_item() -> None:
    source = FakePromotionSource({})

    with pytest.raises(InvalidPromotionQueryError):
        _build_use_case(source, []).execute(USER_ID, ["twaróg", "  "], None)
