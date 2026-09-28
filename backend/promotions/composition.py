from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import httpx

from promotions.application.shop_selection import ShopSelection
from promotions.application.use_cases.check_promotion_access import CheckPromotionAccess
from promotions.application.use_cases.compare_store_promotion_coverage import (
    CompareStorePromotionCoverage,
)
from promotions.application.use_cases.list_favourite_shops import ListFavouriteShops
from promotions.application.use_cases.list_promotion_shops import ListPromotionShops
from promotions.application.use_cases.search_promotions import SearchPromotions
from promotions.application.use_cases.set_favourite_shops import SetFavouriteShops
from promotions.infrastructure.django_favourite_shop_repository import (
    DjangoFavouriteShopRepository,
)
from promotions.infrastructure.django_promotion_permission_reader import (
    DjangoPromotionPermissionReader,
)
from promotions.infrastructure.providers.blix.provider import BlixProvider


@dataclass(frozen=True, slots=True)
class PromotionSourceSettings:
    timeout_seconds: float
    user_agent: str
    search_leaflet_limit: int
    search_result_limit: int


@dataclass(frozen=True, slots=True)
class PromotionOperations:
    list_shops: ListPromotionShops
    set_favourite_shops: SetFavouriteShops
    search: SearchPromotions
    compare_store_coverage: CompareStorePromotionCoverage


@dataclass(frozen=True, slots=True)
class PromotionsModule:
    check_promotion_access: CheckPromotionAccess
    list_favourite_shops: ListFavouriteShops
    source_settings: PromotionSourceSettings

    @contextmanager
    def open_source(self) -> Iterator[PromotionOperations]:
        settings = self.source_settings
        favourites = DjangoFavouriteShopRepository()
        selection = ShopSelection(favourites)
        with httpx.Client(
            timeout=httpx.Timeout(settings.timeout_seconds),
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        ) as client:
            source = BlixProvider(client, settings.search_leaflet_limit)
            yield PromotionOperations(
                list_shops=ListPromotionShops(source),
                set_favourite_shops=SetFavouriteShops(favourites, source),
                search=SearchPromotions(source, selection, settings.search_result_limit),
                compare_store_coverage=CompareStorePromotionCoverage(source, selection),
            )


def build_promotions(source_settings: PromotionSourceSettings) -> PromotionsModule:
    return PromotionsModule(
        check_promotion_access=CheckPromotionAccess(DjangoPromotionPermissionReader()),
        list_favourite_shops=ListFavouriteShops(DjangoFavouriteShopRepository()),
        source_settings=source_settings,
    )
