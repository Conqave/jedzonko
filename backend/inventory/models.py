from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Ingredient, MeasurementUnit
from households.models import Household


class InventoryCategory(models.Model):
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="inventory_categories"
    )
    name = models.CharField(max_length=80)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "name"], name="unique_inventory_category_per_household"
            )
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class InventoryItem(models.Model):
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="inventory_items"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="inventory_items"
    )
    unit = models.ForeignKey(
        MeasurementUnit, on_delete=models.PROTECT, related_name="inventory_items"
    )
    category = models.ForeignKey(
        InventoryCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_items",
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(0)]
    )
    minimum_quantity = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    photo = models.ImageField(upload_to="inventory/", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "ingredient"], name="unique_inventory_item_per_household"
            )
        ]
        indexes = [models.Index(fields=["household", "ingredient"])]
        ordering = ["ingredient__name"]
