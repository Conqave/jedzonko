from shared.measurement_units import MEASUREMENT_UNITS, MeasurementUnitDefinition


class ListMeasurementUnits:
    def execute(self) -> tuple[MeasurementUnitDefinition, ...]:
        return MEASUREMENT_UNITS
