from django.db import models
from django.db.models import Case, F, Q, When

from shared.enums import enum_choices, enum_values
from shared.measurement_units import MEASUREMENT_UNIT_CHOICES, MEASUREMENT_UNIT_CODES
from shopping.domain.shopping_item_status import ShoppingItemStatus

PENDING = ShoppingItemStatus.PENDING.value
PURCHASED = ShoppingItemStatus.PURCHASED.value


class ShoppingList(models.Model):
    household = models.ForeignKey(
        "households.Household", on_delete=models.DB_CASCADE, related_name="shopping_lists"
    )
    name = models.CharField(max_length=120)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    primary_household = models.GeneratedField(
        expression=Case(When(is_primary=True, then=F("household")), default=None),
        output_field=models.BigIntegerField(null=True),
        db_persist=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["primary_household"], name="one_primary_shopping_list_per_household"
            ),
            models.CheckConstraint(condition=~Q(name=""), name="shopping_list_name_not_empty"),
        ]
        ordering = ["-is_primary", "name"]

    def __str__(self) -> str:
        return self.name


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(
        ShoppingList, on_delete=models.DB_CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "catalog.Product",
        null=True,
        blank=True,
        on_delete=models.DB_CASCADE,
        related_name="shopping_list_items",
    )
    ingredient = models.ForeignKey(
        "catalog.Ingredient",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="shopping_list_items",
    )
    free_text = models.CharField(max_length=120, null=True, blank=True)
    unit_code = models.CharField(
        max_length=16, null=True, blank=True, choices=MEASUREMENT_UNIT_CHOICES
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    status = models.CharField(max_length=16, choices=enum_choices(ShoppingItemStatus))
    created_at = models.DateTimeField(auto_now_add=True)
    purchased_at = models.DateTimeField(null=True, blank=True)
    pending_product = models.GeneratedField(
        expression=Case(When(status=PENDING, then=F("product")), default=None),
        output_field=models.BigIntegerField(null=True),
        db_persist=True,
    )
    pending_ingredient = models.GeneratedField(
        expression=Case(When(status=PENDING, then=F("ingredient")), default=None),
        output_field=models.BigIntegerField(null=True),
        db_persist=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(product__isnull=False, ingredient__isnull=True, free_text__isnull=True)
                | Q(product__isnull=True, ingredient__isnull=False, free_text__isnull=True)
                | Q(product__isnull=True, ingredient__isnull=True, free_text__isnull=False),
                name="shopping_item_exactly_one_subject",
            ),
            models.CheckConstraint(
                condition=Q(free_text__isnull=True) | ~Q(free_text=""),
                name="shopping_item_free_text_not_empty",
            ),
            models.CheckConstraint(
                condition=Q(free_text__isnull=False) | Q(unit_code__isnull=False),
                name="shopping_item_measured_subject_has_unit",
            ),
            models.CheckConstraint(
                condition=Q(unit_code__isnull=True) | Q(unit_code__in=MEASUREMENT_UNIT_CODES),
                name="shopping_item_unit_known",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="shopping_item_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(status__in=enum_values(ShoppingItemStatus)),
                name="shopping_item_status_known",
            ),
            models.CheckConstraint(
                condition=Q(status=PURCHASED, purchased_at__isnull=False)
                | Q(status=PENDING, purchased_at__isnull=True),
                name="shopping_item_purchase_time",
            ),
            models.UniqueConstraint(
                fields=["shopping_list", "pending_product"],
                name="one_pending_item_per_product",
            ),
            models.UniqueConstraint(
                fields=["shopping_list", "pending_ingredient"],
                name="one_pending_item_per_ingredient",
            ),
        ]
        indexes = [
            models.Index(fields=["shopping_list", "status"], name="shopping_item_status_idx")
        ]
        ordering = ["created_at", "id"]
