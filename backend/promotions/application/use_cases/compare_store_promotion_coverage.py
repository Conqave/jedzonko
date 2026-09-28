from promotions.application.errors import InvalidPromotionQueryError
from promotions.application.ports.promotion_source import PromotionSource
from promotions.application.shop_selection import ShopSelection
from promotions.domain.coverage import calculate_store_coverage
from promotions.domain.models import PromotionOffer, StorePromotionCoverage


class CompareStorePromotionCoverage:
    def __init__(self, source: PromotionSource, shop_selection: ShopSelection) -> None:
        self._source = source
        self._shop_selection = shop_selection

    def execute(
        self, user_id: int, queries: list[str], requested_shop_slugs: tuple[str, ...] | None
    ) -> list[StorePromotionCoverage]:
        normalized_queries: list[str] = []
        for query in queries:
            normalized_query = query.strip()
            if not normalized_query:
                raise InvalidPromotionQueryError("query must not be empty")
            if normalized_query not in normalized_queries:
                normalized_queries.append(normalized_query)
        if not normalized_queries:
            raise InvalidPromotionQueryError("queries must not be empty")

        shop_slugs = self._shop_selection.resolve(user_id, requested_shop_slugs)
        offers_by_query: dict[str, list[PromotionOffer]] = {
            query: self._source.search_promotions(query, shop_slugs) for query in normalized_queries
        }
        return calculate_store_coverage(offers_by_query)
