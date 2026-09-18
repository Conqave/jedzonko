from promotions.application.ports.favourite_shop_repository import FavouriteShopRepository
from promotions.domain.models import FavouriteShop


class ListFavouriteShops:
    def __init__(self, favourite_shops: FavouriteShopRepository) -> None:
        self._favourite_shops = favourite_shops

    def execute(self, user_id: int) -> list[FavouriteShop]:
        return self._favourite_shops.find_for_user(user_id)
