from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from catalog.models import Ingredient, MeasurementUnit
from households.models import Household


class ShoppingList(models.Model):
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="shopping_lists"
    )
    name = models.CharField(max_length=120)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household"],
                condition=Q(is_primary=True),
                name="unique_primary_shopping_list_per_household",
            )
        ]
        ordering = ["-is_primary", "name"]

    def __str__(self) -> str:
        return self.name


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="items")
    ingredient = models.ForeignKey(
        Ingredient,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shopping_list_items",
    )
    free_text = models.CharField(max_length=120, null=True, blank=True)
    unit = models.ForeignKey(
        MeasurementUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shopping_list_items",
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(0)]
    )
    is_purchased = models.BooleanField(default=False)
    purchased_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(ingredient__isnull=False, free_text__isnull=True)
                    | Q(ingredient__isnull=True, free_text__isnull=False)
                ),
                name="shopping_item_ingredient_xor_free_text",
            ),
            models.UniqueConstraint(
                fields=["shopping_list", "ingredient"],
                condition=Q(is_purchased=False, ingredient__isnull=False),
                name="unique_unpurchased_shopping_item_ingredient",
            ),
        ]
        indexes = [models.Index(fields=["shopping_list", "is_purchased"])]
        ordering = ["created_at", "id"]
