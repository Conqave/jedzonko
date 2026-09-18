from promotions.application.ports.promotion_source import PromotionSource
from promotions.domain.coverage import calculate_store_coverage
from promotions.domain.models import PromotionOffer, StorePromotionCoverage


class CompareStorePromotionCoverage:
    def __init__(self, source: PromotionSource) -> None:
        self._source = source

    def execute(self, queries: list[str]) -> list[StorePromotionCoverage]:
        normalized_queries: list[str] = []
        for query in queries:
            normalized_query = query.strip()
            if not normalized_query:
                raise ValueError("query must not be empty")
            if normalized_query not in normalized_queries:
                normalized_queries.append(normalized_query)
        if not normalized_queries:
            raise ValueError("queries must not be empty")

        offers_by_query: dict[str, list[PromotionOffer]] = {
            query: self._source.search_promotions(query) for query in normalized_queries
        }
        return calculate_store_coverage(offers_by_query)
