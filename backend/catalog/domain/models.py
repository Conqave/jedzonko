from dataclasses import dataclass

from catalog.domain.measurement import MeasurementDimension


@dataclass(frozen=True, slots=True)
class IngredientSummary:
    id: int
    name: str
    default_unit_code: str


@dataclass(frozen=True, slots=True)
class MeasurementUnitSummary:
    code: str
    name: str
    dimension: MeasurementDimension
