from promotions.application.errors import InvalidShopSelectionError
from promotions.application.ports.favourite_shop_repository import FavouriteShopRepository


def normalize_shop_slugs(shop_slugs: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for shop_slug in shop_slugs:
        candidate = shop_slug.strip().casefold()
        if not candidate:
            raise InvalidShopSelectionError("shop slug must not be empty")
        if candidate not in normalized:
            normalized.append(candidate)
    return tuple(normalized)


class ShopSelection:
    def __init__(self, favourite_shops: FavouriteShopRepository) -> None:
        self._favourite_shops = favourite_shops

    def resolve(
        self, user_id: int, requested_shop_slugs: tuple[str, ...] | None
    ) -> tuple[str, ...]:
        if requested_shop_slugs is not None:
            return normalize_shop_slugs(requested_shop_slugs)
        favourites = self._favourite_shops.find_for_user(user_id)
        return normalize_shop_slugs(tuple(favourite.slug for favourite in favourites))
