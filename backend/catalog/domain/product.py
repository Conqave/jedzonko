from dataclasses import dataclass
from decimal import Decimal

from catalog.domain.errors import InvalidProductPackageError, UnknownMeasurementUnitError
from shared.measurement_units import find_measurement_unit


def require_known_unit(unit_code: str) -> str:
    if find_measurement_unit(unit_code) is None:
        raise UnknownMeasurementUnitError(unit_code)
    return unit_code


@dataclass(frozen=True, slots=True)
class ProductPackage:

    quantity: Decimal
    unit_code: str

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidProductPackageError("A package holds a positive quantity.")
        require_known_unit(self.unit_code)


@dataclass(frozen=True, slots=True)
class Product:
    id: int
    household_id: int
    name: str
    default_unit_code: str
    is_food: bool
    package: ProductPackage | None


@dataclass(frozen=True, slots=True)
class ProductTag:
    ingredient_id: int
    name: str


@dataclass(frozen=True, slots=True)
class ProductListing:
    product: Product
    tags: tuple[ProductTag, ...]
    open_proposal_count: int


@dataclass(frozen=True, slots=True)
class ProductIdentity:

    product_id: int
    name: str
    tags: tuple[ProductTag, ...]
    package: ProductPackage | None
