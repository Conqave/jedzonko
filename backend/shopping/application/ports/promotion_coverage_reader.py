from abc import ABC, abstractmethod

from shopping.domain.promotion_split import ShopPromotions


class PromotionCoverageReader(ABC):
    @abstractmethod
    def get_shop_promotions(
        self, user_id: int, item_names: tuple[str, ...], shop_slugs: tuple[str, ...]
    ) -> list[ShopPromotions]:
        raise NotImplementedError
