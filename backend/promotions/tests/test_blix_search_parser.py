from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from promotions.application.ports.promotion_source import PromotionSourceContractError
from promotions.infrastructure.providers.blix.parser import BlixSearchParser

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_search_results() -> None:
    html = (FIXTURES / "blix_search_twarog.html").read_text(encoding="utf-8")

    offers = BlixSearchParser("https://blix.pl").parse(html)

    assert len(offers) == 1
    offer = offers[0]
    assert offer.provider_offer_id == "69fe2d14e"
    assert offer.name == "Twaróg wiejski chudy Mlekovita"
    assert offer.shop_name == "Tomi Markt"
    assert offer.shop_url == "https://blix.pl/sklep/tomi-markt/"
    assert offer.product_brand_name == "Mlekovita"
    assert offer.price == Decimal("2.99")
    assert offer.leaflet_provider_id == "523785"
    assert offer.leaflet_url == ("https://blix.pl/sklep/tomi-markt/gazetka/523785/?pageNumber=5")
    assert offer.page_number == 5
    assert offer.valid_from == date(2026, 9, 17)
    assert offer.valid_until == date(2026, 9, 29)


def test_missing_window_offers_is_contract_error() -> None:
    with pytest.raises(PromotionSourceContractError):
        BlixSearchParser("https://blix.pl").parse("<html></html>")


def test_parse_offer_without_price() -> None:
    html = (FIXTURES / "blix_search_offer_without_price.html").read_text(encoding="utf-8")

    offers = BlixSearchParser("https://blix.pl").parse(html)

    assert len(offers) == 1
    assert offers[0].price is None
    assert offers[0].name == "Mielonka królewska Polonus"


def test_non_numeric_price_is_contract_error() -> None:
    html = (FIXTURES / "blix_search_offer_without_price.html").read_text(encoding="utf-8")
    broken_html = html.replace('"price":null', '"price":"249"')

    with pytest.raises(PromotionSourceContractError):
        BlixSearchParser("https://blix.pl").parse(broken_html)


def test_no_results_page_returns_empty_list() -> None:
    html = (FIXTURES / "blix_search_no_results.html").read_text(encoding="utf-8")

    assert BlixSearchParser("https://blix.pl").parse(html) == []


def test_offer_without_hash_has_no_provider_offer_id() -> None:
    html = (FIXTURES / "blix_search_twarog.html").read_text(encoding="utf-8")
    html_without_hash = html.replace('"hash":"69fe2d14e"', '"hash":null')

    offers = BlixSearchParser("https://blix.pl").parse(html_without_hash)

    assert offers[0].provider_offer_id is None
    assert offers[0].name == "Twaróg wiejski chudy Mlekovita"


def test_page_without_offers_and_without_no_results_marker_is_contract_error() -> None:
    with pytest.raises(PromotionSourceContractError):
        BlixSearchParser("https://blix.pl").parse("<html><body><h1>Promocje</h1></body></html>")


def test_malformed_offer_payload_is_contract_error() -> None:
    html = (FIXTURES / "blix_search_twarog.html").read_text(encoding="utf-8")
    broken_html = html.replace('"leafletId":523785', '"leafletId":"523785"')

    with pytest.raises(PromotionSourceContractError):
        BlixSearchParser("https://blix.pl").parse(broken_html)
