from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from promotions.application.ports.promotion_source import PromotionSource
from promotions.domain.models import Leaflet, LeafletPage, PromotionOffer, Shop


def build_offer(
    name: str,
    shop_name: str,
    provider_offer_id: str | None,
    price: str | None = "9.99",
) -> PromotionOffer:
    slug = shop_name.casefold()
    return PromotionOffer(
        provider_offer_id=provider_offer_id,
        name=name,
        shop_name=shop_name,
        shop_url=f"https://blix.pl/sklep/{slug}/",
        image_url=f"https://img.blix.pl/{provider_offer_id}.jpg",
        product_brand_name=None,
        price=None if price is None else Decimal(price),
        leaflet_provider_id="1000",
        leaflet_url=f"https://blix.pl/sklep/{slug}/gazetka/1000/?pageNumber=1",
        page_number=1,
        valid_from=date(2026, 9, 14),
        valid_until=date(2026, 9, 20),
    )


class FakePromotionSource(PromotionSource):
    def __init__(self, offers_by_query: Mapping[str, Sequence[PromotionOffer]]) -> None:
        self._offers_by_query = offers_by_query
        self.received_queries: list[str] = []

    def list_shops(self) -> list[Shop]:
        raise NotImplementedError

    def list_leaflets(self, shop_name: str) -> list[Leaflet]:
        raise NotImplementedError

    def list_leaflet_pages(self, leaflet_provider_id: str) -> list[LeafletPage]:
        raise NotImplementedError

    def search_promotions(self, query: str) -> list[PromotionOffer]:
        self.received_queries.append(query)
        return list(self._offers_by_query.get(query, []))


class FailingPromotionSource(PromotionSource):
    def __init__(self, error: Exception) -> None:
        self._error = error

    def list_shops(self) -> list[Shop]:
        raise NotImplementedError

    def list_leaflets(self, shop_name: str) -> list[Leaflet]:
        raise NotImplementedError

    def list_leaflet_pages(self, leaflet_provider_id: str) -> list[LeafletPage]:
        raise NotImplementedError

    def search_promotions(self, query: str) -> list[PromotionOffer]:
        raise self._error
