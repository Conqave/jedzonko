from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import assert_never

from shared.measurement import MeasurementDimension, Quantity
from shared.measurement_units import BASE_UNIT_CODES

GRAMS_PER_CALORIE_REFERENCE = Decimal(100)
PIECE_UNIT_CODE = BASE_UNIT_CODES[MeasurementDimension.COUNT]


class InvalidNutritionFactsError(Exception):
    pass


class UncountedReason(StrEnum):
    NO_AMOUNT = "no_amount"
    NO_CALORIES = "no_calories"
    NO_PIECE_WEIGHT = "no_piece_weight"
    NO_DENSITY = "no_density"
    NO_PACKAGE_WEIGHT = "no_package_weight"


@dataclass(frozen=True, slots=True)
class NutritionFacts:
    kcal_per_100g: Decimal | None
    grams_per_piece: Decimal | None
    grams_per_ml: Decimal | None

    def __post_init__(self) -> None:
        if self.kcal_per_100g is not None and self.kcal_per_100g < 0:
            raise InvalidNutritionFactsError("Calories per 100 g cannot be negative.")
        if self.grams_per_piece is not None and self.grams_per_piece <= 0:
            raise InvalidNutritionFactsError("A piece weighs more than nothing.")
        if self.grams_per_ml is not None and self.grams_per_ml <= 0:
            raise InvalidNutritionFactsError("A density is positive.")


@dataclass(frozen=True, slots=True)
class CountedKcal:
    kcal: Decimal
    is_estimate: bool


@dataclass(frozen=True, slots=True)
class _Grams:
    amount: Decimal
    is_estimate: bool


def count_kcal(
    quantity: Quantity | None, facts: NutritionFacts | None
) -> CountedKcal | UncountedReason:
    if quantity is None:
        return UncountedReason.NO_AMOUNT
    if facts is None or facts.kcal_per_100g is None:
        return UncountedReason.NO_CALORIES
    grams = _to_grams(quantity, facts)
    if isinstance(grams, UncountedReason):
        return grams
    kcal = grams.amount * facts.kcal_per_100g / GRAMS_PER_CALORIE_REFERENCE
    return CountedKcal(kcal=kcal, is_estimate=grams.is_estimate)


def _to_grams(quantity: Quantity, facts: NutritionFacts) -> _Grams | UncountedReason:
    base_amount = quantity.amount * quantity.unit.factor_to_base
    dimension = quantity.unit.dimension
    match dimension:
        case MeasurementDimension.MASS:
            return _Grams(amount=base_amount, is_estimate=False)
        case MeasurementDimension.VOLUME:
            if facts.grams_per_ml is None:
                return UncountedReason.NO_DENSITY
            return _Grams(amount=base_amount * facts.grams_per_ml, is_estimate=True)
        case MeasurementDimension.COUNT:
            if quantity.unit.code != PIECE_UNIT_CODE:
                return UncountedReason.NO_PACKAGE_WEIGHT
            if facts.grams_per_piece is None:
                return UncountedReason.NO_PIECE_WEIGHT
            return _Grams(amount=base_amount * facts.grams_per_piece, is_estimate=True)
        case _:
            assert_never(dimension)
