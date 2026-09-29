from catalog.application.errors import ProductNotFoundError
from catalog.application.ports.product_repository import ProductRepository
from shared.household_membership import HouseholdMembershipReader, require_membership


class DeleteProduct:
    def __init__(self, products: ProductRepository, memberships: HouseholdMembershipReader) -> None:
        self._products = products
        self._memberships = memberships

    def execute(self, user_id: int, product_id: int) -> None:
        product = self._products.find(product_id)
        if product is None:
            raise ProductNotFoundError
        require_membership(self._memberships, user_id, product.household_id)
        self._products.delete(product_id)
