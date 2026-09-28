from dataclasses import dataclass

from promotions.application.use_cases.compare_store_promotion_coverage import (
    CompareStorePromotionCoverage,
)
from promotions.application.use_cases.list_promotion_shops import ListPromotionShops
from promotions.application.use_cases.search_promotions import SearchPromotions
from promotions.application.use_cases.set_favourite_shops import SetFavouriteShops


@dataclass(frozen=True, slots=True)
class PromotionOperations:
    list_shops: ListPromotionShops
    set_favourite_shops: SetFavouriteShops
    search: SearchPromotions
    compare_store_coverage: CompareStorePromotionCoverage
