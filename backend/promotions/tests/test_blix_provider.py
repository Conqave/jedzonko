from pathlib import Path

import httpx
import pytest

from promotions.application.ports.promotion_source import PromotionSourceUnavailable
from promotions.infrastructure.providers.blix.provider import BlixProvider

FIXTURES = Path(__file__).parent / "fixtures"


def test_search_promotions_uses_public_search_page() -> None:
    html = (FIXTURES / "blix_search_twarog.html").read_text(encoding="utf-8")

    def handle_request(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/szukaj/"
        assert request.url.params["szukaj"] == "twaróg chudy"
        return httpx.Response(200, text=html, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))
    provider = BlixProvider(client)

    offers = provider.search_promotions("  twaróg chudy  ")

    assert len(offers) == 1
    assert offers[0].shop_name == "Tomi Markt"


def test_search_promotions_returns_empty_list_for_no_results_page() -> None:
    html = (FIXTURES / "blix_search_no_results.html").read_text(encoding="utf-8")

    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))

    assert BlixProvider(client).search_promotions("nieistniejacy produkt") == []


def test_search_promotions_maps_transport_failure_to_provider_unavailable() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))

    with pytest.raises(PromotionSourceUnavailable):
        BlixProvider(client).search_promotions("twaróg")


def test_search_promotions_maps_http_error_to_provider_unavailable() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))

    with pytest.raises(PromotionSourceUnavailable):
        BlixProvider(client).search_promotions("twaróg")
