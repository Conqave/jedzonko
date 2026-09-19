from collections.abc import Iterator
from contextlib import contextmanager

import httpx
from django.conf import settings

from promotions.application.ports.favourite_shop_repository import FavouriteShopRepository
from promotions.application.ports.promotion_source import PromotionSource
from promotions.application.shop_selection import ShopSelection
from promotions.infrastructure.django_favourite_shop_repository import (
    DjangoFavouriteShopRepository,
)
from promotions.infrastructure.providers.blix.provider import BlixProvider


@contextmanager
def open_promotion_source() -> Iterator[PromotionSource]:
    with httpx.Client(
        timeout=httpx.Timeout(settings.PROMOTIONS_HTTP_TIMEOUT_SECONDS),
        headers={"User-Agent": settings.PROMOTIONS_HTTP_USER_AGENT},
        follow_redirects=True,
    ) as client:
        yield BlixProvider(client, settings.PROMOTIONS_SEARCH_LEAFLET_LIMIT)


def build_favourite_shop_repository() -> FavouriteShopRepository:
    return DjangoFavouriteShopRepository()


def build_shop_selection() -> ShopSelection:
    return ShopSelection(build_favourite_shop_repository())


def build_search_result_limit() -> int:
    limit = settings.PROMOTIONS_SEARCH_RESULT_LIMIT
    if not isinstance(limit, int):
        raise TypeError("PROMOTIONS_SEARCH_RESULT_LIMIT must be an integer")
    return limit
