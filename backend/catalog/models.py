from django.db import models
from django.db.models import Case, F, Q, When

from catalog.domain.candidate import CandidateStatus
from catalog.domain.ingredient import IngredientNameKind, IngredientNameSource
from catalog.domain.names import MAX_NAME_LENGTH
from catalog.domain.product_ingredient import ProductIngredientSource, ProductIngredientStatus
from shared.enums import enum_choices, enum_values
from shared.measurement_units import MEASUREMENT_UNIT_CHOICES, MEASUREMENT_UNIT_CODES


class Product(models.Model):
    household = models.ForeignKey(
        "households.Household", on_delete=models.DB_CASCADE, related_name="products"
    )
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=120)
    default_unit_code = models.CharField(max_length=16, choices=MEASUREMENT_UNIT_CHOICES)
    is_food = models.BooleanField(default=True)
    package_quantity = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    package_unit_code = models.CharField(
        max_length=16, null=True, blank=True, choices=MEASUREMENT_UNIT_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "normalized_name"], name="unique_product_per_household"
            ),
            models.CheckConstraint(condition=~Q(name=""), name="product_name_not_empty"),
            models.CheckConstraint(
                condition=~Q(normalized_name=""), name="product_normalized_name_not_empty"
            ),
            models.CheckConstraint(
                condition=Q(default_unit_code__in=MEASUREMENT_UNIT_CODES),
                name="product_default_unit_known",
            ),
            models.CheckConstraint(
                condition=Q(package_unit_code__isnull=True)
                | Q(package_unit_code__in=MEASUREMENT_UNIT_CODES),
                name="product_package_unit_known",
            ),
            models.CheckConstraint(
                condition=Q(package_quantity__isnull=True, package_unit_code__isnull=True)
                | Q(package_quantity__isnull=False, package_unit_code__isnull=False),
                name="product_package_quantity_requires_unit",
            ),
            models.CheckConstraint(
                condition=Q(package_quantity__isnull=True) | Q(package_quantity__gt=0),
                name="product_package_quantity_positive",
            ),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(name=""), name="ingredient_name_not_empty"),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class IngredientName(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.DB_CASCADE, related_name="names")
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    normalized_name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    kind = models.CharField(max_length=16, choices=enum_choices(IngredientNameKind))
    source = models.CharField(max_length=16, choices=enum_choices(IngredientNameSource))
    canonical_ingredient = models.GeneratedField(
        expression=Case(
            When(kind=IngredientNameKind.CANONICAL.value, then=F("ingredient")), default=None
        ),
        output_field=models.BigIntegerField(null=True),
        db_persist=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["canonical_ingredient"], name="one_canonical_name_per_ingredient"
            ),
            models.CheckConstraint(condition=~Q(name=""), name="ingredient_name_text_not_empty"),
            models.CheckConstraint(
                condition=~Q(normalized_name=""), name="ingredient_normalized_name_not_empty"
            ),
            models.CheckConstraint(
                condition=Q(kind__in=enum_values(IngredientNameKind)),
                name="ingredient_name_kind_known",
            ),
            models.CheckConstraint(
                condition=Q(source__in=enum_values(IngredientNameSource)),
                name="ingredient_name_source_known",
            ),
        ]
        ordering = ["ingredient_id", "kind", "name"]

    def __str__(self) -> str:
        return self.name


class ProductIngredient(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.DB_CASCADE, related_name="ingredient_links"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.DO_NOTHING, related_name="product_links"
    )
    status = models.CharField(max_length=16, choices=enum_choices(ProductIngredientStatus))
    source = models.CharField(max_length=16, choices=enum_choices(ProductIngredientSource))
    model_name = models.CharField(max_length=80, null=True, blank=True)
    proposed_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    confirmed_product = models.GeneratedField(
        expression=Case(
            When(status=ProductIngredientStatus.CONFIRMED.value, then=F("product")),
            default=None,
        ),
        output_field=models.BigIntegerField(null=True),
        db_persist=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "ingredient"], name="one_link_per_product_ingredient"
            ),
            models.UniqueConstraint(
                fields=["confirmed_product"], name="one_confirmed_ingredient_per_product"
            ),
            models.CheckConstraint(
                condition=Q(status__in=enum_values(ProductIngredientStatus)),
                name="product_ingredient_status_known",
            ),
            models.CheckConstraint(
                condition=Q(source__in=enum_values(ProductIngredientSource)),
                name="product_ingredient_source_known",
            ),
            models.CheckConstraint(
                condition=Q(
                    source=ProductIngredientSource.MODEL.value,
                    model_name__isnull=False,
                    proposed_at__isnull=False,
                )
                | (~Q(source=ProductIngredientSource.MODEL.value) & Q(model_name__isnull=True)),
                name="product_ingredient_model_provenance",
            ),
            models.CheckConstraint(
                condition=Q(status=ProductIngredientStatus.PROPOSED.value, decided_at__isnull=True)
                | (~Q(status=ProductIngredientStatus.PROPOSED.value) & Q(decided_at__isnull=False)),
                name="product_ingredient_decision_time",
            ),
        ]
        ordering = ["product_id", "ingredient_id"]


class IngredientNameCandidate(models.Model):

    name = models.CharField(max_length=MAX_NAME_LENGTH)
    normalized_name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    source = models.CharField(max_length=16, choices=enum_choices(IngredientNameSource))
    status = models.CharField(max_length=16, choices=enum_choices(CandidateStatus))
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(name=""), name="candidate_name_not_empty"),
            models.CheckConstraint(
                condition=~Q(normalized_name=""), name="candidate_normalized_name_not_empty"
            ),
            models.CheckConstraint(
                condition=Q(source__in=enum_values(IngredientNameSource)),
                name="candidate_source_known",
            ),
            models.CheckConstraint(
                condition=Q(status__in=enum_values(CandidateStatus)), name="candidate_status_known"
            ),
            models.CheckConstraint(
                condition=Q(status=CandidateStatus.PENDING.value, decided_at__isnull=True)
                | (~Q(status=CandidateStatus.PENDING.value) & Q(decided_at__isnull=False)),
                name="candidate_decision_time",
            ),
        ]
        ordering = ["status", "name"]

    def __str__(self) -> str:
        return self.name
