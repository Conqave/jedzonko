from abc import ABC, abstractmethod

from promotions.domain.models import PromotionOffer, Shop


class PromotionSource(ABC):
    @abstractmethod
    def list_shops(self) -> list[Shop]:
        raise NotImplementedError

    @abstractmethod
    def search_promotions(self, query: str, shop_slugs: tuple[str, ...]) -> list[PromotionOffer]:
        raise NotImplementedError
