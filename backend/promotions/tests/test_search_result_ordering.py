from decimal import Decimal

import pytest

from promotions.domain.models import PromotionOffer
from promotions.domain.search_results import build_search_results
from promotions.tests.fakes import build_offer


def _on_page(offer: PromotionOffer, leaflet_provider_id: str, page_number: int) -> PromotionOffer:
    return PromotionOffer(
        provider_offer_id=offer.provider_offer_id,
        name=offer.name,
        shop_name=offer.shop_name,
        shop_slug=offer.shop_slug,
        shop_url=offer.shop_url,
        image_url=offer.image_url,
        product_brand_name=offer.product_brand_name,
        price=offer.price,
        leaflet_provider_id=leaflet_provider_id,
        leaflet_url=offer.leaflet_url,
        page_number=page_number,
        valid_from=offer.valid_from,
        valid_until=offer.valid_until,
    )


def test_exact_duplicates_across_leaflet_pages_collapse_into_one_offer() -> None:
    offer = build_offer("Mleko UHT 3,2%", "Biedronka", None, "3.49")
    duplicates = [
        _on_page(offer, "1000", 1),
        _on_page(offer, "1000", 7),
        _on_page(offer, "1001", 3),
    ]

    result = build_search_results(duplicates, 200)

    assert len(result) == 1
    assert result[0].leaflet_provider_id == "1000"
    assert result[0].page_number == 1


def test_duplicates_differing_only_by_diacritics_and_case_collapse() -> None:
    offers = [
        build_offer("Mleko Łaciate", "Biedronka", None, "3.49"),
        build_offer("MLEKO LACIATE", "Biedronka", None, "3.49"),
    ]

    assert len(build_search_results(offers, 200)) == 1


def test_same_product_at_two_prices_stays_separate() -> None:
    offers = [
        build_offer("Mleko UHT 3,2%", "Biedronka", None, "3.49"),
        build_offer("Mleko UHT 3,2%", "Biedronka", None, "2.99"),
    ]

    result = build_search_results(offers, 200)

    assert [offer.price for offer in result] == [Decimal("2.99"), Decimal("3.49")]


def test_same_product_in_two_shops_stays_separate() -> None:
    offers = [
        build_offer("Mleko UHT 3,2%", "Lidl", None, "3.49"),
        build_offer("Mleko UHT 3,2%", "Biedronka", None, "3.49"),
    ]

    result = build_search_results(offers, 200)

    assert [offer.shop_name for offer in result] == ["Biedronka", "Lidl"]


def test_null_price_variant_is_dropped_when_the_same_product_has_a_price() -> None:
    offers = [
        build_offer("Mleko UHT 3,2%", "Biedronka", None, None),
        build_offer("Mleko UHT 3,2%", "Biedronka", None, "3.49"),
    ]

    result = build_search_results(offers, 200)

    assert [offer.price for offer in result] == [Decimal("3.49")]


def test_null_price_offers_are_kept_when_no_priced_variant_exists() -> None:
    offers = [
        build_offer("Mleko UHT 3,2%", "Biedronka", None, None),
        build_offer("Mleko UHT 3,2%", "Biedronka", None, None),
    ]

    result = build_search_results(offers, 200)

    assert [offer.price for offer in result] == [None]


def test_duplicate_collapsing_keeps_the_offer_carrying_more_information() -> None:
    without_identifier = build_offer("Mleko UHT 3,2%", "Biedronka", None, "3.49")
    with_identifier = build_offer("Mleko UHT 3,2%", "Biedronka", "hash-9", "3.49")

    assert build_search_results([without_identifier, with_identifier], 200) == [with_identifier]
    assert build_search_results([with_identifier, without_identifier], 200) == [with_identifier]


def test_results_are_ordered_by_shop_then_product_then_price() -> None:
    offers = [
        build_offer("Mleko UHT 3,2%", "Lidl", None, "3.49"),
        build_offer("Mleko UHT 3,2%", "Biedronka", None, "3.49"),
        build_offer("Mleko UHT 3,2%", "Biedronka", None, "2.99"),
        build_offer("Masło extra", "Biedronka", None, "7.99"),
        build_offer("Mleko UHT 3,2%", "Biedronka", None, None),
        build_offer("Mleko bez laktozy", "Biedronka", None, "4.49"),
    ]

    result = build_search_results(offers, 200)

    assert [(offer.shop_name, offer.name, offer.price) for offer in result] == [
        ("Biedronka", "Masło extra", Decimal("7.99")),
        ("Biedronka", "Mleko bez laktozy", Decimal("4.49")),
        ("Biedronka", "Mleko UHT 3,2%", Decimal("2.99")),
        ("Biedronka", "Mleko UHT 3,2%", Decimal("3.49")),
        ("Lidl", "Mleko UHT 3,2%", Decimal("3.49")),
    ]


def test_ordering_does_not_depend_on_input_order() -> None:
    offers = [
        build_offer("Mleko UHT 3,2%", "Lidl", None, "3.49"),
        build_offer("Masło extra", "Biedronka", "hash-2", "7.99"),
        build_offer("Mleko bez laktozy", "Biedronka", None, "4.49"),
    ]

    assert build_search_results(offers, 200) == build_search_results(list(reversed(offers)), 200)


def test_the_result_limit_is_applied_after_ordering() -> None:
    offers = [
        build_offer("Mleko UHT 3,2%", "Lidl", None, "3.49"),
        build_offer("Masło extra", "Biedronka", None, "7.99"),
        build_offer("Mleko bez laktozy", "Biedronka", None, "4.49"),
    ]

    result = build_search_results(offers, 2)

    assert [offer.name for offer in result] == ["Masło extra", "Mleko bez laktozy"]


def test_a_limit_below_one_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_search_results([], 0)
