from households.application.ports.product_repository import ProductRepository
from households.domain.product import ProductSummary


class FindHouseholdProduct:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def execute(self, household_id: int, product_id: int) -> ProductSummary | None:
        return self._repository.find_product(household_id, product_id)
