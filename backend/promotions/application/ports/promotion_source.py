from abc import ABC, abstractmethod

from promotions.domain.models import Leaflet, LeafletPage, PromotionOffer, Shop


class PromotionSourceError(Exception):
    pass


class PromotionSourceUnavailable(PromotionSourceError):
    pass


class PromotionSourceContractError(PromotionSourceError):
    pass


class PromotionSource(ABC):
    @abstractmethod
    def list_shops(self) -> list[Shop]:
        raise NotImplementedError

    @abstractmethod
    def list_leaflets(self, shop_name: str) -> list[Leaflet]:
        raise NotImplementedError

    @abstractmethod
    def list_leaflet_pages(self, leaflet_provider_id: str) -> list[LeafletPage]:
        raise NotImplementedError

    @abstractmethod
    def search_promotions(self, query: str, shop_slugs: tuple[str, ...]) -> list[PromotionOffer]:
        raise NotImplementedError
