from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from promotions.application.ports.favourite_shop_repository import FavouriteShopRepository
from promotions.application.ports.promotion_source import PromotionSource
from promotions.domain.models import FavouriteShop, PromotionOffer, Shop

SHOPS = [
    Shop(name="Biedronka", slug="biedronka", url="https://blix.pl/sklep/biedronka/"),
    Shop(name="Carrefour", slug="carrefour", url="https://blix.pl/sklep/carrefour/"),
    Shop(name="Lidl", slug="lidl", url="https://blix.pl/sklep/lidl/"),
]


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
        shop_slug=slug,
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
        self.received_shop_slugs: list[tuple[str, ...]] = []

    def list_shops(self) -> list[Shop]:
        return list(SHOPS)

    def search_promotions(self, query: str, shop_slugs: tuple[str, ...]) -> list[PromotionOffer]:
        self.received_queries.append(query)
        self.received_shop_slugs.append(shop_slugs)
        offers = self._offers_by_query.get(query, [])
        if shop_slugs:
            return [offer for offer in offers if offer.shop_slug in shop_slugs]
        return list(offers)


class FailingPromotionSource(PromotionSource):
    def __init__(self, error: Exception) -> None:
        self._error = error

    def list_shops(self) -> list[Shop]:
        raise self._error

    def search_promotions(self, query: str, shop_slugs: tuple[str, ...]) -> list[PromotionOffer]:
        raise self._error


class FakeFavouriteShopRepository(FavouriteShopRepository):
    def __init__(self, favourites_by_user: Mapping[int, Sequence[FavouriteShop]]) -> None:
        self._favourites_by_user = {
            user_id: list(favourites) for user_id, favourites in favourites_by_user.items()
        }

    def find_for_user(self, user_id: int) -> list[FavouriteShop]:
        return list(self._favourites_by_user.get(user_id, []))

    def replace_for_user(self, user_id: int, favourite_shops: list[FavouriteShop]) -> None:
        self._favourites_by_user[user_id] = list(favourite_shops)
