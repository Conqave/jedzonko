from pathlib import Path

import pytest

from promotions.application.ports.promotion_source import PromotionSourceContractError
from promotions.infrastructure.providers.blix.parser import BlixSearchParser

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_leaflet_hits() -> None:
    html = (FIXTURES / "blix_search_leaflets.html").read_text(encoding="utf-8")

    hits = BlixSearchParser("https://blix.pl").parse(html)

    assert [(hit.shop_name, hit.shop_slug, hit.leaflet_id, hit.page_number) for hit in hits] == [
        ("Biedronka", "biedronka", 524175, 69),
        ("Carrefour", "carrefour", 523008, 6),
        ("Kaufland", "kaufland", 524220, 17),
    ]
    assert hits[0].leaflet_url == "https://blix.pl/sklep/biedronka/gazetka/524175/?pageNumber=69"


def test_no_results_page_returns_empty_list() -> None:
    html = (FIXTURES / "blix_search_no_results.html").read_text(encoding="utf-8")

    assert BlixSearchParser("https://blix.pl").parse(html) == []


def test_page_without_hits_and_without_no_results_marker_is_contract_error() -> None:
    with pytest.raises(PromotionSourceContractError):
        BlixSearchParser("https://blix.pl").parse("<html><body><h1>Promocje</h1></body></html>")


def test_non_numeric_leaflet_id_is_contract_error() -> None:
    html = (FIXTURES / "blix_search_leaflets.html").read_text(encoding="utf-8")
    broken_html = html.replace('data-leaflet-id="524175"', 'data-leaflet-id="not-a-number"')

    with pytest.raises(PromotionSourceContractError):
        BlixSearchParser("https://blix.pl").parse(broken_html)


def test_missing_brand_slug_is_contract_error() -> None:
    html = (FIXTURES / "blix_search_leaflets.html").read_text(encoding="utf-8")
    broken_html = html.replace('data-brand-slug="biedronka"', 'data-brand-slug=""')

    with pytest.raises(PromotionSourceContractError):
        BlixSearchParser("https://blix.pl").parse(broken_html)


def test_leaflet_link_without_page_number_is_contract_error() -> None:
    html = (FIXTURES / "blix_search_leaflets.html").read_text(encoding="utf-8")
    broken_html = html.replace(
        'href="https://blix.pl/sklep/biedronka/gazetka/524175/?pageNumber=69"',
        'href="https://blix.pl/sklep/biedronka/gazetka/524175/"',
    )

    with pytest.raises(PromotionSourceContractError):
        BlixSearchParser("https://blix.pl").parse(broken_html)
