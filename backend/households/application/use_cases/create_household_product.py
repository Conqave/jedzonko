from households.application.access import HouseholdAccessPolicy
from households.application.errors import MeasurementUnitNotFoundError
from households.application.ports.product_repository import ProductRepository
from households.domain.product import ProductSummary
from shared.measurement_units import find_measurement_unit


class CreateHouseholdProduct:
    def __init__(self, repository: ProductRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(
        self, user_id: int, household_id: int, name: str, default_unit_code: str, is_food: bool
    ) -> ProductSummary:
        self._access.require_membership(user_id, household_id)
        if find_measurement_unit(default_unit_code) is None:
            raise MeasurementUnitNotFoundError
        return self._repository.create_product(household_id, name, default_unit_code, is_food)
