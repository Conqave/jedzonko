from django.conf import settings
from django.db import models
from django.db.models import Q


class PromotionAccess(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_promotions", "Can view promotions")]


class FavouriteShop(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DB_CASCADE,
        related_name="favourite_promotion_shops",
    )
    shop_slug = models.CharField(max_length=120)
    shop_name = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "shop_slug"], name="unique_favourite_shop"),
            models.CheckConstraint(
                condition=~Q(shop_slug=""), name="favourite_shop_slug_not_empty"
            ),
            models.CheckConstraint(
                condition=~Q(shop_name=""), name="favourite_shop_name_not_empty"
            ),
        ]
        indexes = [models.Index(fields=["user"], name="favourite_shop_user_idx")]
