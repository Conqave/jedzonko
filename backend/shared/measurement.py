from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class MeasurementDimension(StrEnum):
    MASS = "mass"
    VOLUME = "volume"
    COUNT = "count"


class IncompatibleUnitsError(Exception):
    def __init__(self, source: str, target: str) -> None:
        super().__init__(f"Cannot convert {source} to {target}.")
        self.source = source
        self.target = target


@dataclass(frozen=True, slots=True)
class MeasurementUnit:
    code: str
    dimension: MeasurementDimension
    factor_to_base: Decimal


@dataclass(frozen=True, slots=True)
class Quantity:
    amount: Decimal
    unit: MeasurementUnit

    def convert_to(self, target: MeasurementUnit) -> Quantity:
        if target.dimension is not self.unit.dimension:
            raise IncompatibleUnitsError(self.unit.code, target.code)
        base_amount = self.amount * self.unit.factor_to_base
        return Quantity(amount=base_amount / target.factor_to_base, unit=target)

    def is_compatible_with(self, other: Quantity) -> bool:
        return self.unit.dimension is other.unit.dimension

    def subtract(self, other: Quantity) -> Quantity:
        return Quantity(amount=self.amount - other.convert_to(self.unit).amount, unit=self.unit)

    def add(self, other: Quantity) -> Quantity:
        return Quantity(amount=self.amount + other.convert_to(self.unit).amount, unit=self.unit)
