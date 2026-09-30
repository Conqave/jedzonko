from decimal import Decimal
from enum import StrEnum

from shared.measurement import MeasurementDimension, Quantity

GRAMS_PER_CALORIE_REFERENCE = Decimal(100)


class UncountedReason(StrEnum):
    NO_AMOUNT = "no_amount"
    NOT_BY_MASS = "not_by_mass"
    NO_CALORIES = "no_calories"


def count_kcal(
    quantity: Quantity | None, kcal_per_100g: Decimal | None
) -> Decimal | UncountedReason:
    if quantity is None:
        return UncountedReason.NO_AMOUNT
    if quantity.unit.dimension is not MeasurementDimension.MASS:
        return UncountedReason.NOT_BY_MASS
    if kcal_per_100g is None:
        return UncountedReason.NO_CALORIES
    grams = quantity.amount * quantity.unit.factor_to_base
    return grams * kcal_per_100g / GRAMS_PER_CALORIE_REFERENCE
