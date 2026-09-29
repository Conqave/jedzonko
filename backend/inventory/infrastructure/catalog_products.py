from catalog.application.use_cases.find_household_product import FindHouseholdProduct
from inventory.application.ports.product_directory import ProductDirectory


class CatalogProductDirectory(ProductDirectory):
    def __init__(self, find_product: FindHouseholdProduct) -> None:
        self._find_product = find_product

    def is_household_product(self, household_id: int, product_id: int) -> bool:
        return self._find_product.execute(household_id, product_id) is not None
