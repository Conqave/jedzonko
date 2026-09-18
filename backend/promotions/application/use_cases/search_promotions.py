from promotions.application.ports.promotion_source import PromotionSource
from promotions.application.shop_selection import ShopSelection
from promotions.domain.models import PromotionOffer


class SearchPromotions:
    def __init__(self, source: PromotionSource, shop_selection: ShopSelection) -> None:
        self._source = source
        self._shop_selection = shop_selection

    def execute(
        self, user_id: int, query: str, requested_shop_slugs: tuple[str, ...] | None
    ) -> list[PromotionOffer]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")
        shop_slugs = self._shop_selection.resolve(user_id, requested_shop_slugs)
        return self._source.search_promotions(normalized_query, shop_slugs)
