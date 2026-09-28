from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from households.domain.tag_proposal_state import TagProposalState
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
    ingredient_tags = models.ManyToManyField(
        "IngredientTag", through="ProductTag", related_name="products", blank=True
    )
    package_quantity = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    package_unit_code = models.CharField(
        max_length=16,
        blank=True,
        choices=[(item.code, item.name) for item in MEASUREMENT_UNITS],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "normalized_name"], name="unique_product_per_household"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(package_quantity__isnull=True, package_unit_code="")
                    | models.Q(package_quantity__isnull=False) & ~models.Q(package_unit_code="")
                ),
                name="product_package_quantity_requires_unit",
            ),
        ]
        indexes = [models.Index(fields=["household", "normalized_name"])]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class IngredientTag(models.Model):
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=120, unique=True)
    source = models.CharField(max_length=32, default="ania_gotuje")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ProductTag(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_tags")
    ingredient_tag = models.ForeignKey(
        IngredientTag, on_delete=models.CASCADE, related_name="product_tags"
    )
    source = models.CharField(max_length=32, default="manual")
    is_verified = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "ingredient_tag"], name="unique_product_ingredient_tag"
            )
        ]
        ordering = ["ingredient_tag__name"]


class TagProposal(models.Model):
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="tag_proposals"
    )
    requirement_name = models.CharField(max_length=120)
    normalized_requirement_name = models.CharField(max_length=120)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="tag_proposals")
    model_name = models.CharField(max_length=80)
    state = models.CharField(
        max_length=16, choices=[(item.value, item.name.title()) for item in TagProposalState]
    )
    created_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "normalized_requirement_name", "product"],
                name="unique_alias_proposal_pair",
            )
        ]
        indexes = [models.Index(fields=["household", "state"])]
        ordering = ["household_id", "requirement_name", "id"]

    def __str__(self) -> str:
        return f"{self.requirement_name} -> {self.product_id}"
