from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from promotions.application.errors import (
    PromotionSourceContractError,
    PromotionSourceUnavailableError,
)
from promotions.infrastructure.providers.blix.provider import BlixProvider

FIXTURES = Path(__file__).parent / "fixtures"
SEARCH_HTML = (FIXTURES / "blix_search_leaflets.html").read_text(encoding="utf-8")
LEAFLET_JSON = (FIXTURES / "blix_getleaflet_biedronka.json").read_text(encoding="utf-8")
SHOPS_HTML = (FIXTURES / "shops.html").read_text(encoding="utf-8")


def _build_provider(
    requested_paths: list[str],
    search_leaflet_limit: int = 5,
    leaflet_body: str = LEAFLET_JSON,
) -> BlixProvider:
    def handle_request(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        if request.url.path == "/szukaj/":
            return httpx.Response(200, text=SEARCH_HTML, request=request)
        if request.url.path.startswith("/getleaflet/"):
            return httpx.Response(
                200,
                text=leaflet_body,
                headers={"Content-Type": "application/json"},
                request=request,
            )
        raise AssertionError(f"unexpected request path: {request.url.path}")

    client = httpx.Client(transport=httpx.MockTransport(handle_request))
    return BlixProvider(client, search_leaflet_limit)


def test_search_queries_public_search_page_then_matching_leaflets() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=1)

    offers = provider.search_promotions("  twaróg  ", ())

    assert requested_paths[0] == "/szukaj/"
    assert requested_paths[1] == "/getleaflet/biedronka/524175/"
    assert [offer.name for offer in offers] == [
        "Twaróg półtłusty wiejski Piątnica",
        "Serek twarogowy Kids World Minecraft",
    ]


def test_search_drops_offers_that_do_not_match_the_query() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=1)

    offers = provider.search_promotions("twaróg", ())

    names = [offer.name for offer in offers]
    assert "Krem do twarzy multi-odżywczy Eveline 24k Gold & Diamenty" not in names
    assert "Ser gouda w plastrach Światowid 1 kg" not in names


def test_search_maps_offer_fields_from_leaflet_payload() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=1)

    offer = provider.search_promotions("twaróg", ())[0]

    assert offer.provider_offer_id == "662b5414b"
    assert offer.shop_name == "Biedronka"
    assert offer.shop_slug == "biedronka"
    assert offer.shop_url == "https://blix.pl/sklep/biedronka/"
    assert offer.product_brand_name == "Piątnica"
    assert offer.price == Decimal("3.99")
    assert offer.leaflet_provider_id == "524175"
    assert offer.leaflet_url == "https://blix.pl/sklep/biedronka/gazetka/524175/?pageNumber=68"
    assert offer.page_number == 68
    assert offer.valid_from.isoformat() == "2026-09-14"
    assert offer.valid_until.isoformat() == "2026-09-19"


def test_search_keeps_null_price_and_null_provider_offer_id() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=1)

    offer = provider.search_promotions("serek twarogowy", ())[0]

    assert offer.name == "Serek twarogowy Kids World Minecraft"
    assert offer.provider_offer_id is None
    assert offer.price == Decimal("1.69")


def test_search_keeps_null_price_for_offers_without_price() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=1)

    offer = provider.search_promotions("gouda", ())[0]

    assert offer.price is None
    assert offer.provider_offer_id is None


def test_search_filters_shops_before_fetching_leaflets() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=5)

    provider.search_promotions("twaróg", ("biedronka", "kaufland"))

    assert requested_paths == [
        "/szukaj/",
        "/getleaflet/biedronka/524175/",
        "/getleaflet/kaufland/524220/",
    ]
    assert "/getleaflet/carrefour/523008/" not in requested_paths


def test_search_ignores_unknown_shop_slugs_without_failing() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=5)

    offers = provider.search_promotions("twaróg", ("biedornka", "lidl"))

    assert offers == []
    assert requested_paths == ["/szukaj/"]


def test_search_bounds_the_number_of_fetched_leaflets() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=2)

    provider.search_promotions("twaróg", ())

    assert requested_paths == [
        "/szukaj/",
        "/getleaflet/biedronka/524175/",
        "/getleaflet/carrefour/523008/",
    ]


def test_search_returns_empty_list_for_no_results_page() -> None:
    html = (FIXTURES / "blix_search_no_results.html").read_text(encoding="utf-8")

    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))

    assert BlixProvider(client, 5).search_promotions("nieistniejacy produkt", ()) == []


def test_search_maps_malformed_search_html_to_contract_error() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body><h1>Promocje</h1></body></html>")

    client = httpx.Client(transport=httpx.MockTransport(handle_request))

    with pytest.raises(PromotionSourceContractError):
        BlixProvider(client, 5).search_promotions("twaróg", ())


def test_search_maps_malformed_leaflet_json_to_contract_error() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=1, leaflet_body="not json")

    with pytest.raises(PromotionSourceContractError):
        provider.search_promotions("twaróg", ())


def test_search_maps_leaflet_payload_without_product_offers_to_contract_error() -> None:
    requested_paths: list[str] = []
    provider = _build_provider(requested_paths, search_leaflet_limit=1, leaflet_body='{"id": 1}')

    with pytest.raises(PromotionSourceContractError):
        provider.search_promotions("twaróg", ())


def test_search_maps_transport_failure_to_provider_unavailable() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))

    with pytest.raises(PromotionSourceUnavailableError):
        BlixProvider(client, 5).search_promotions("twaróg", ())


def test_search_maps_http_error_to_provider_unavailable() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))

    with pytest.raises(PromotionSourceUnavailableError):
        BlixProvider(client, 5).search_promotions("twaróg", ())


def _build_shops_provider(shops_html: str) -> BlixProvider:
    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=shops_html, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))
    return BlixProvider(client, 5)


def test_list_shops_lists_each_shop_once_across_page_sections() -> None:
    provider = _build_shops_provider(SHOPS_HTML)

    shops = provider.list_shops()

    assert [(shop.name, shop.slug, shop.url) for shop in shops] == [
        ("Lidl", "lidl", "https://blix.pl/sklep/lidl"),
        ("Biedronka", "biedronka", "https://blix.pl/sklep/biedronka"),
        ("Jysk", "jysk", "https://blix.pl/sklep/jysk"),
    ]


def test_list_shops_rejects_one_slug_listed_with_different_names() -> None:
    shops_html = (
        '<div class="section-n__items section-n__items--brands">'
        '<a title="Lidl" href="/sklep/lidl"></a></div>'
        '<div class="section-n__items section-n__items--brands">'
        '<a title="Lidl Plus" href="/sklep/lidl"></a></div>'
    )
    provider = _build_shops_provider(shops_html)

    with pytest.raises(PromotionSourceContractError):
        provider.list_shops()
