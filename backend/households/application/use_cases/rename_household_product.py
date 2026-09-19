from households.application.access import HouseholdAccessPolicy
from households.application.errors import DuplicateProductError
from households.application.ports.product_repository import ProductRepository
from households.domain.product import ProductSummary


class RenameHouseholdProduct:
    def __init__(self, repository: ProductRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(
        self, user_id: int, household_id: int, product_id: int, name: str
    ) -> ProductSummary:
        self._access.require_membership(user_id, household_id)
        existing = self._repository.find_product_by_name(household_id, name)
        if existing is not None and existing.id != product_id:
            raise DuplicateProductError
        return self._repository.rename_product(household_id, product_id, name)
