from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from households.models import Household, Product
from shared.measurement_units import MEASUREMENT_UNITS

UNIT_CODE_CHOICES = [(item.code, item.name) for item in MEASUREMENT_UNITS]


class ShoppingList(models.Model):
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="shopping_lists"
    )
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PrimaryShoppingList(models.Model):
    household = models.OneToOneField(
        Household, on_delete=models.CASCADE, related_name="primary_shopping_list"
    )
    shopping_list = models.OneToOneField(
        ShoppingList, on_delete=models.CASCADE, related_name="primary_marker"
    )


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shopping_list_items",
    )
    free_text = models.CharField(max_length=120, null=True, blank=True)
    unit_code = models.CharField(max_length=16, null=True, blank=True, choices=UNIT_CODE_CHOICES)
    quantity = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(product__isnull=False, free_text__isnull=True)
                    | Q(product__isnull=True, free_text__isnull=False)
                ),
                name="shopping_item_product_xor_free_text",
            ),
            models.UniqueConstraint(
                fields=["shopping_list", "product"],
                name="unique_pending_shopping_item_product",
            ),
        ]
        ordering = ["created_at", "id"]


class PurchasedShoppingItem(models.Model):
    shopping_list = models.ForeignKey(
        ShoppingList, on_delete=models.CASCADE, related_name="purchased_items"
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="purchased_shopping_items",
    )
    free_text = models.CharField(max_length=120, null=True, blank=True)
    unit_code = models.CharField(max_length=16, null=True, blank=True, choices=UNIT_CODE_CHOICES)
    quantity = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField()
    purchased_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(product__isnull=False, free_text__isnull=True)
                    | Q(product__isnull=True, free_text__isnull=False)
                ),
                name="purchased_shopping_item_product_xor_free_text",
            )
        ]
        indexes = [models.Index(fields=["shopping_list", "purchased_at"])]
        ordering = ["created_at", "id"]
