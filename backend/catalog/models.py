from django.core.validators import MinValueValidator
from django.db import models

from catalog.domain.measurement import MeasurementDimension


class MeasurementUnit(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=64)
    dimension = models.CharField(
        max_length=16, choices=[(item.value, item.name.title()) for item in MeasurementDimension]
    )
    factor_to_base = models.DecimalField(
        max_digits=18, decimal_places=6, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class Ingredient(models.Model):
    name = models.CharField(max_length=120, unique=True)
    default_unit = models.ForeignKey(
        MeasurementUnit, on_delete=models.PROTECT, related_name="ingredients"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
