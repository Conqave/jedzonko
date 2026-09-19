from households.application.access import HouseholdAccessPolicy
from households.application.ports.product_repository import ProductRepository
from households.domain.product import ProductSummary


class ListHouseholdProducts:
    def __init__(self, repository: ProductRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(
        self, user_id: int, household_id: int, name_query: str | None
    ) -> list[ProductSummary]:
        self._access.require_membership(user_id, household_id)
        return self._repository.list_products(household_id, name_query)
