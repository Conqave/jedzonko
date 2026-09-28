from catalog.application.errors import DuplicateProductError, ProductNotFoundError
from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.names import CatalogName
from catalog.domain.product import Product, ProductPackage
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager


class UpdateProduct:
    def __init__(
        self,
        products: ProductRepository,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._products = products
        self._memberships = memberships
        self._transactions = transactions

    def execute(
        self, user_id: int, product_id: int, name: str, package: ProductPackage | None
    ) -> Product:
        text = CatalogName.parse(name)
        with self._transactions.atomic():
            product = self._products.find(product_id)
            if product is None:
                raise ProductNotFoundError
            require_membership(self._memberships, user_id, product.household_id)
            same_name = self._products.find_by_name(product.household_id, text.normalized_name)
            if same_name is not None and same_name.id != product_id:
                raise DuplicateProductError
            return self._products.update(product_id, text, package)
