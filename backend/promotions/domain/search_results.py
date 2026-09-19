from collections.abc import Sequence
from decimal import Decimal

from promotions.domain.models import PromotionOffer
from shared.text import normalize_text

_ZERO = Decimal(0)


def build_search_results(offers: Sequence[PromotionOffer], limit: int) -> list[PromotionOffer]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    collapsed = _collapse_duplicates(offers)
    collapsed.sort(key=_ordering_key)
    return collapsed[:limit]


def _collapse_duplicates(offers: Sequence[PromotionOffer]) -> list[PromotionOffer]:
    best_by_identity: dict[tuple[str, str, Decimal | None], PromotionOffer] = {}
    for offer in offers:
        identity = _identity_key(offer)
        current = best_by_identity.get(identity)
        if current is None or _information_rank(offer) < _information_rank(current):
            best_by_identity[identity] = offer

    priced_products = {
        (shop_slug, product) for shop_slug, product, price in best_by_identity if price is not None
    }
    return [
        offer
        for (shop_slug, product, price), offer in best_by_identity.items()
        if price is not None or (shop_slug, product) not in priced_products
    ]


def _identity_key(offer: PromotionOffer) -> tuple[str, str, Decimal | None]:
    return (offer.shop_slug, _normalized_product(offer), offer.price)


def _information_rank(offer: PromotionOffer) -> tuple[int, int, str, int, str]:
    return (
        1 if offer.provider_offer_id is None else 0,
        1 if offer.product_brand_name is None else 0,
        offer.leaflet_provider_id,
        offer.page_number,
        offer.provider_offer_id or "",
    )


def _ordering_key(offer: PromotionOffer) -> tuple[str, str, str, bool, Decimal, str, str, int]:
    return (
        offer.shop_name,
        offer.shop_slug,
        _normalized_product(offer),
        offer.price is None,
        _ZERO if offer.price is None else offer.price,
        offer.name,
        offer.leaflet_provider_id,
        offer.page_number,
    )


def _normalized_product(offer: PromotionOffer) -> str:
    return normalize_text(offer.name)
