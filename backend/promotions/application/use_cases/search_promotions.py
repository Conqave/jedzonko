from promotions.application.errors import InvalidPromotionQueryError
from promotions.application.ports.promotion_source import PromotionSource
from promotions.application.shop_selection import ShopSelection
from promotions.domain.models import PromotionOffer
from promotions.domain.search_results import build_search_results


class SearchPromotions:
    def __init__(
        self, source: PromotionSource, shop_selection: ShopSelection, result_limit: int
    ) -> None:
        self._source = source
        self._shop_selection = shop_selection
        self._result_limit = result_limit

    def execute(
        self, user_id: int, query: str, requested_shop_slugs: tuple[str, ...] | None
    ) -> list[PromotionOffer]:
        normalized_query = query.strip()
        if not normalized_query:
            raise InvalidPromotionQueryError("query must not be empty")
        shop_slugs = self._shop_selection.resolve(user_id, requested_shop_slugs)
        offers = self._source.search_promotions(normalized_query, shop_slugs)
        return build_search_results(offers, self._result_limit)
