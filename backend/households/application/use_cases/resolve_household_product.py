from households.application.errors import MeasurementUnitNotFoundError
from households.application.ports.product_repository import ProductRepository
from households.domain.product import ProductSummary
from shared.measurement_units import find_measurement_unit


class ResolveHouseholdProduct:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def execute(
        self, household_id: int, name: str, default_unit_code: str, is_food: bool
    ) -> ProductSummary:
        if find_measurement_unit(default_unit_code) is None:
            raise MeasurementUnitNotFoundError
        return self._repository.get_or_create_product(
            household_id, name, default_unit_code, is_food
        )
