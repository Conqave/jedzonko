from django.conf import settings
from django.db import models

from shared.measurement_units import MEASUREMENT_UNITS


class Household(models.Model):
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class HouseholdMembership(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="household_memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["household", "user"], name="unique_household_member")
        ]
        ordering = ["household_id", "user_id"]


class Product(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=120)
    default_unit_code = models.CharField(
        max_length=16, choices=[(item.code, item.name) for item in MEASUREMENT_UNITS]
    )
    is_food = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "normalized_name"], name="unique_product_per_household"
            )
        ]
        indexes = [models.Index(fields=["household", "normalized_name"])]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
