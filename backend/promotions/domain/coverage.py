from collections.abc import Mapping, Sequence

from promotions.domain.models import PromotionOffer, StorePromotionCoverage


def calculate_store_coverage(
    offers_by_query: Mapping[str, Sequence[PromotionOffer]],
) -> list[StorePromotionCoverage]:
    shop_urls: dict[str, str] = {}
    queries_by_shop: dict[str, list[str]] = {}
    offers_by_shop: dict[str, list[PromotionOffer]] = {}

    for query, offers in offers_by_query.items():
        for offer in offers:
            shop_urls.setdefault(offer.shop_name, offer.shop_url)
            matched_queries = queries_by_shop.setdefault(offer.shop_name, [])
            if query not in matched_queries:
                matched_queries.append(query)
            offers_by_shop.setdefault(offer.shop_name, []).append(offer)

    coverage = [
        StorePromotionCoverage(
            shop_name=shop_name,
            shop_url=shop_urls[shop_name],
            matched_query_count=len(queries_by_shop[shop_name]),
            matched_queries=tuple(queries_by_shop[shop_name]),
            offers=tuple(offers_by_shop[shop_name]),
        )
        for shop_name in offers_by_shop
    ]
    coverage.sort(key=lambda item: (-item.matched_query_count, item.shop_name))
    return coverage
