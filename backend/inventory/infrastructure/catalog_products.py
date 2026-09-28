from catalog.application.errors import DuplicateProductError
from catalog.application.use_cases.find_household_product import FindHouseholdProduct
from catalog.application.use_cases.rename_product import RenameProduct
from catalog.domain.errors import InvalidNameError
from inventory.application.errors import DuplicateProductNameError, InvalidProductNameError
from inventory.application.ports.product_directory import ProductDirectory
from inventory.application.ports.product_renamer import ProductRenamer


class CatalogProductDirectory(ProductDirectory):
    def __init__(self, find_product: FindHouseholdProduct) -> None:
        self._find_product = find_product

    def is_household_product(self, household_id: int, product_id: int) -> bool:
        return self._find_product.execute(household_id, product_id) is not None


class CatalogProductRenamer(ProductRenamer):
    def __init__(self, rename_product: RenameProduct) -> None:
        self._rename_product = rename_product

    def set_product_name(self, user_id: int, product_id: int, name: str) -> None:
        try:
            self._rename_product.execute(user_id, product_id, name)
        except DuplicateProductError as error:
            raise DuplicateProductNameError from error
        except InvalidNameError as error:
            raise InvalidProductNameError from error
