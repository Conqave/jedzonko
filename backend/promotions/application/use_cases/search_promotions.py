from promotions.application.ports.promotion_source import PromotionSource
from promotions.domain.models import PromotionOffer


class SearchPromotions:
    def __init__(self, source: PromotionSource) -> None:
        self._source = source

    def execute(self, query: str) -> list[PromotionOffer]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")
        return self._source.search_promotions(normalized_query)
