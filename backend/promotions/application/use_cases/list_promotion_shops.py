from promotions.application.ports.promotion_source import PromotionSource
from promotions.domain.models import Shop


class ListPromotionShops:
    def __init__(self, source: PromotionSource) -> None:
        self._source = source

    def execute(self) -> list[Shop]:
        return self._source.list_shops()
