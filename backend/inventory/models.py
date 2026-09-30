from django.db import models
from django.db.models import Q

from shared.measurement_units import MEASUREMENT_UNIT_CHOICES, MEASUREMENT_UNIT_CODES


class InventoryItem(models.Model):
    product = models.OneToOneField(
        "catalog.Product", on_delete=models.DB_CASCADE, related_name="inventory_item"
    )
    unit_code = models.CharField(max_length=16, choices=MEASUREMENT_UNIT_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    minimum_quantity = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    photo = models.ImageField(upload_to="inventory/", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(unit_code__in=MEASUREMENT_UNIT_CODES),
                name="inventory_item_unit_known",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0), name="inventory_item_quantity_not_negative"
            ),
            models.CheckConstraint(
                condition=Q(minimum_quantity__isnull=True) | Q(minimum_quantity__gte=0),
                name="inventory_item_minimum_not_negative",
            ),
        ]
        ordering = ["product__name"]
