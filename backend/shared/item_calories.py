from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from shared.measurement import MeasurementDimension, Quantity
from shared.nutrition import PIECE_UNIT_CODE, NutritionFacts, UncountedReason, count_kcal


class TagGap(StrEnum):
    NO_TAG = "no_tag"
    SEVERAL_TAGS = "several_tags"


@dataclass(frozen=True, slots=True)
class SubjectNutrition:
    facts: NutritionFacts | TagGap
    package: Quantity | None

    @classmethod
    def untagged(cls) -> SubjectNutrition:
        return cls(facts=TagGap.NO_TAG, package=None)


@dataclass(frozen=True, slots=True)
class ItemCalories:
    kcal: Decimal | None
    kcal_per_100g: Decimal | None
    is_estimate: bool
    uncounted_reason: TagGap | UncountedReason | None

    def __post_init__(self) -> None:
        if (self.kcal is None) == (self.uncounted_reason is None):
            raise AssertionError("Item calories are either counted or say why they are not.")
        if self.is_estimate and self.kcal is None:
            raise AssertionError("Only counted calories can be an estimate.")


def count_item_calories(quantity: Quantity | None, nutrition: SubjectNutrition) -> ItemCalories:
    facts = nutrition.facts
    if isinstance(facts, TagGap):
        return ItemCalories(
            kcal=None, kcal_per_100g=None, is_estimate=False, uncounted_reason=facts
        )
    unpacked = _unpack(quantity, nutrition.package)
    counted = count_kcal(unpacked, facts)
    if isinstance(counted, UncountedReason):
        return ItemCalories(
            kcal=None,
            kcal_per_100g=facts.kcal_per_100g,
            is_estimate=False,
            uncounted_reason=counted,
        )
    return ItemCalories(
        kcal=counted.kcal,
        kcal_per_100g=facts.kcal_per_100g,
        is_estimate=counted.is_estimate,
        uncounted_reason=None,
    )


def _unpack(quantity: Quantity | None, package: Quantity | None) -> Quantity | None:
    if quantity is None or package is None:
        return quantity
    unit = quantity.unit
    is_package = unit.dimension is MeasurementDimension.COUNT and unit.code != PIECE_UNIT_CODE
    if not is_package:
        return quantity
    package_count = quantity.amount * unit.factor_to_base
    return Quantity(amount=package_count * package.amount, unit=package.unit)
