from django.db import transaction

from promotions.application.ports.favourite_shop_repository import FavouriteShopRepository
from promotions.domain.models import FavouriteShop
from promotions.models import FavouriteShop as FavouriteShopRow


class DjangoFavouriteShopRepository(FavouriteShopRepository):
    def find_for_user(self, user_id: int) -> list[FavouriteShop]:
        rows = FavouriteShopRow.objects.filter(user_id=user_id).order_by("shop_name", "shop_slug")
        return [FavouriteShop(name=row.shop_name, slug=row.shop_slug) for row in rows]

    def replace_for_user(self, user_id: int, favourite_shops: list[FavouriteShop]) -> None:
        with transaction.atomic():
            FavouriteShopRow.objects.filter(user_id=user_id).delete()
            FavouriteShopRow.objects.bulk_create(
                [
                    FavouriteShopRow(
                        user_id=user_id,
                        shop_slug=favourite_shop.slug,
                        shop_name=favourite_shop.name,
                    )
                    for favourite_shop in favourite_shops
                ]
            )
