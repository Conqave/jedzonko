import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PromotionAccess",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
            ],
            options={
                "permissions": [("view_promotions", "Can view promotions")],
                "managed": False,
                "default_permissions": (),
            },
        ),
        migrations.CreateModel(
            name="FavouriteShop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("shop_slug", models.CharField(max_length=120)),
                ("shop_name", models.CharField(max_length=120)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="favourite_promotion_shops",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [models.Index(fields=["user"], name="favourite_shop_user_idx")],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("user", "shop_slug"), name="unique_favourite_shop"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("shop_slug", ""), _negated=True),
                        name="favourite_shop_slug_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("shop_name", ""), _negated=True),
                        name="favourite_shop_name_not_empty",
                    ),
                ],
            },
        ),
    ]
