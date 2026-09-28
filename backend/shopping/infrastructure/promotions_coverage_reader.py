from collections.abc import Callable
from contextlib import AbstractContextManager

from promotions.application.errors import (
    PromotionSourceContractError,
    PromotionSourceUnavailableError,
)
from promotions.application.use_cases.check_promotion_access import CheckPromotionAccess
from promotions.application.use_cases.promotion_operations import PromotionOperations
from shopping.application.errors import PromotionsNotAllowedError, PromotionsUnavailableError
from shopping.application.ports.promotion_coverage_reader import PromotionCoverageReader
from shopping.domain.promotion_split import ShopPromotions


class PromotionsCoverageReader(PromotionCoverageReader):
    def __init__(
        self,
        open_promotions: Callable[[], AbstractContextManager[PromotionOperations]],
        check_access: CheckPromotionAccess,
    ) -> None:
        self._open_promotions = open_promotions
        self._check_access = check_access

    def get_shop_promotions(
        self, user_id: int, item_names: tuple[str, ...], shop_slugs: tuple[str, ...]
    ) -> list[ShopPromotions]:
        if not self._check_access.execute(user_id):
            raise PromotionsNotAllowedError
        queries = list(item_names)
        try:
            with self._open_promotions() as promotions:
                coverage = promotions.compare_store_coverage.execute(user_id, queries, shop_slugs)
        except (PromotionSourceUnavailableError, PromotionSourceContractError) as error:
            raise PromotionsUnavailableError from error
        return [
            ShopPromotions(
                shop_slug=shop.shop_slug,
                shop_name=shop.shop_name,
                promoted_names=frozenset(shop.matched_queries),
            )
            for shop in coverage
        ]
