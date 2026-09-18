import pytest

from promotions.application.shop_selection import ShopSelection
from promotions.application.use_cases.search_promotions import SearchPromotions
from promotions.domain.models import FavouriteShop
from promotions.tests.fakes import FakeFavouriteShopRepository, FakePromotionSource, build_offer

USER_ID = 7


def _build_use_case(
    source: FakePromotionSource, favourites: list[FavouriteShop]
) -> SearchPromotions:
    repository = FakeFavouriteShopRepository({USER_ID: favourites})
    return SearchPromotions(source, ShopSelection(repository))


def test_search_promotions_returns_provider_offers() -> None:
    offer = build_offer("Twaróg półtłusty", "Biedronka", "hash-1")
    source = FakePromotionSource({"twaróg": [offer]})

    result = _build_use_case(source, []).execute(USER_ID, "twaróg", None)

    assert result == [offer]


def test_search_promotions_trims_query_before_calling_provider() -> None:
    source = FakePromotionSource({"twaróg": []})

    _build_use_case(source, []).execute(USER_ID, "  twaróg  ", None)

    assert source.received_queries == ["twaróg"]


def test_search_promotions_normalizes_the_requested_shop_selection() -> None:
    source = FakePromotionSource({"twaróg": []})

    _build_use_case(source, []).execute(USER_ID, "twaróg", (" Lidl ", "lidl", "biedronka"))

    assert source.received_shop_slugs == [("lidl", "biedronka")]


def test_search_promotions_restricts_results_to_the_requested_shops() -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "hash-1"),
                build_offer("Twaróg", "Carrefour", "hash-2"),
            ]
        }
    )

    result = _build_use_case(source, []).execute(USER_ID, "twaróg", ("biedronka",))

    assert [offer.shop_name for offer in result] == ["Biedronka"]


def test_search_promotions_falls_back_to_saved_favourites() -> None:
    source = FakePromotionSource({"twaróg": []})
    favourites = [
        FavouriteShop(name="Lidl", slug="lidl"),
        FavouriteShop(name="Biedronka", slug="biedronka"),
    ]

    _build_use_case(source, favourites).execute(USER_ID, "twaróg", None)

    assert source.received_shop_slugs == [("lidl", "biedronka")]


def test_search_promotions_prefers_explicit_shops_over_favourites() -> None:
    source = FakePromotionSource({"twaróg": []})
    favourites = [FavouriteShop(name="Lidl", slug="lidl")]

    _build_use_case(source, favourites).execute(USER_ID, "twaróg", ("carrefour",))

    assert source.received_shop_slugs == [("carrefour",)]


def test_search_promotions_uses_all_shops_without_favourites() -> None:
    source = FakePromotionSource({"twaróg": []})

    _build_use_case(source, []).execute(USER_ID, "twaróg", None)

    assert source.received_shop_slugs == [()]


def test_search_promotions_returns_empty_result_without_matches() -> None:
    source = FakePromotionSource({})

    assert _build_use_case(source, []).execute(USER_ID, "twaróg", None) == []


def test_search_promotions_rejects_blank_query() -> None:
    source = FakePromotionSource({})

    with pytest.raises(ValueError):
        _build_use_case(source, []).execute(USER_ID, "   ", None)


def test_search_promotions_rejects_blank_shop_slug() -> None:
    source = FakePromotionSource({})

    with pytest.raises(ValueError):
        _build_use_case(source, []).execute(USER_ID, "twaróg", ("  ",))
