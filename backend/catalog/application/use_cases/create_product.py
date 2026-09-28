from catalog.application.errors import DuplicateProductError
from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.names import CatalogName
from catalog.domain.product import Product, ProductPackage, require_known_unit
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager


class CreateProduct:
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
        self,
        user_id: int,
        household_id: int,
        name: str,
        default_unit_code: str,
        is_food: bool,
        package: ProductPackage | None,
    ) -> Product:
        require_membership(self._memberships, user_id, household_id)
        text = CatalogName.parse(name)
        require_known_unit(default_unit_code)
        with self._transactions.atomic():
            if self._products.find_by_name(household_id, text.normalized_name) is not None:
                raise DuplicateProductError
            return self._products.create(household_id, text, default_unit_code, is_food, package)
