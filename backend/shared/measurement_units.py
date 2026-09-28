from dataclasses import dataclass
from decimal import Decimal

from shared.measurement import MeasurementDimension, MeasurementUnit


@dataclass(frozen=True, slots=True)
class MeasurementUnitDefinition:
    code: str
    name: str
    dimension: MeasurementDimension
    factor_to_base: Decimal

    def to_unit(self) -> MeasurementUnit:
        return MeasurementUnit(
            code=self.code, dimension=self.dimension, factor_to_base=self.factor_to_base
        )


MEASUREMENT_UNITS: tuple[MeasurementUnitDefinition, ...] = (
    MeasurementUnitDefinition("g", "gram", MeasurementDimension.MASS, Decimal("1")),
    MeasurementUnitDefinition("kg", "kilogram", MeasurementDimension.MASS, Decimal("1000")),
    MeasurementUnitDefinition("ml", "mililitr", MeasurementDimension.VOLUME, Decimal("1")),
    MeasurementUnitDefinition("l", "litr", MeasurementDimension.VOLUME, Decimal("1000")),
    MeasurementUnitDefinition("szt", "sztuka", MeasurementDimension.COUNT, Decimal("1")),
    MeasurementUnitDefinition("opak", "opakowanie", MeasurementDimension.COUNT, Decimal("1")),
)

_DEFINITIONS_BY_CODE = {definition.code: definition for definition in MEASUREMENT_UNITS}

MEASUREMENT_UNIT_CODES: tuple[str, ...] = tuple(_DEFINITIONS_BY_CODE)


def find_measurement_unit(code: str) -> MeasurementUnit | None:
    definition = _DEFINITIONS_BY_CODE.get(code)
    return None if definition is None else definition.to_unit()


MEASUREMENT_UNIT_CHOICES: tuple[tuple[str, str], ...] = tuple(
    (definition.code, definition.name) for definition in MEASUREMENT_UNITS
)
