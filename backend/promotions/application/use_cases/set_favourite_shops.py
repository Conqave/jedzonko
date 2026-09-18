from promotions.application.ports.favourite_shop_repository import FavouriteShopRepository
from promotions.application.ports.promotion_source import PromotionSource
from promotions.application.shop_selection import normalize_shop_slugs
from promotions.domain.models import FavouriteShop


class UnknownShopError(Exception):
    def __init__(self, shop_slug: str) -> None:
        super().__init__(f"unknown shop: {shop_slug}")
        self.shop_slug = shop_slug


class SetFavouriteShops:
    def __init__(self, favourite_shops: FavouriteShopRepository, source: PromotionSource) -> None:
        self._favourite_shops = favourite_shops
        self._source = source

    def execute(self, user_id: int, shop_slugs: tuple[str, ...]) -> list[FavouriteShop]:
        requested_slugs = normalize_shop_slugs(shop_slugs)
        if not requested_slugs:
            self._favourite_shops.replace_for_user(user_id, [])
            return []

        names_by_slug = {shop.slug: shop.name for shop in self._source.list_shops()}
        selected: list[FavouriteShop] = []
        for shop_slug in requested_slugs:
            if shop_slug not in names_by_slug:
                raise UnknownShopError(shop_slug)
            selected.append(FavouriteShop(name=names_by_slug[shop_slug], slug=shop_slug))

        self._favourite_shops.replace_for_user(user_id, selected)
        return self._favourite_shops.find_for_user(user_id)
