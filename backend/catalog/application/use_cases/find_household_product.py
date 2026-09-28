from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.product import Product


class FindHouseholdProduct:

    def __init__(self, products: ProductRepository) -> None:
        self._products = products

    def execute(self, household_id: int, product_id: int) -> Product | None:
        product = self._products.find(product_id)
        if product is None or product.household_id != household_id:
            return None
        return product
