from abc import ABC, abstractmethod

from promotions.domain.models import FavouriteShop


class FavouriteShopRepository(ABC):
    @abstractmethod
    def find_for_user(self, user_id: int) -> list[FavouriteShop]:
        raise NotImplementedError

    @abstractmethod
    def replace_for_user(self, user_id: int, favourite_shops: list[FavouriteShop]) -> None:
        raise NotImplementedError
