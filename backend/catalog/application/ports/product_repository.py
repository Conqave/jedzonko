from abc import ABC, abstractmethod

from catalog.domain.names import CatalogName
from catalog.domain.product import Product, ProductListing, ProductPackage


class ProductRepository(ABC):
    @abstractmethod
    def find(self, product_id: int) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_name(self, household_id: int, normalized_name: str) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    def list_listings(
        self, household_id: int, normalized_search: str | None
    ) -> list[ProductListing]:
        raise NotImplementedError

    @abstractmethod
    def list_for_household(self, household_id: int) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    def list_unclassified(self) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        household_id: int,
        name: CatalogName,
        default_unit_code: str,
        is_food: bool,
        package: ProductPackage | None,
    ) -> Product:
        raise NotImplementedError

    @abstractmethod
    def update(self, product_id: int, name: CatalogName, package: ProductPackage | None) -> Product:
        raise NotImplementedError
