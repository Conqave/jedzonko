from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Shop:
    name: str
    slug: str
    url: str


@dataclass(frozen=True, slots=True)
class PromotionOffer:
    provider_offer_id: str | None
    name: str
    shop_name: str
    shop_slug: str
    shop_url: str
    image_url: str
    product_brand_name: str | None
    price: Decimal | None
    leaflet_provider_id: str
    leaflet_url: str
    page_number: int
    valid_from: date
    valid_until: date


@dataclass(frozen=True, slots=True)
class StorePromotionCoverage:
    shop_name: str
    shop_slug: str
    shop_url: str
    matched_query_count: int
    matched_queries: tuple[str, ...]
    offers: tuple[PromotionOffer, ...]


@dataclass(frozen=True, slots=True)
class FavouriteShop:
    name: str
    slug: str
