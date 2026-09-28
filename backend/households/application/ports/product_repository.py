from abc import ABC, abstractmethod

from households.domain.product import ProductSummary
from households.domain.product_names import ProductNames


class ProductRepository(ABC):
    @abstractmethod
    def list_products(self, household_id: int, name_query: str | None) -> list[ProductSummary]:
        raise NotImplementedError

    @abstractmethod
    def list_product_names(self, household_id: int) -> list[ProductNames]:
        raise NotImplementedError

    @abstractmethod
    def find_product(self, household_id: int, product_id: int) -> ProductSummary | None:
        raise NotImplementedError

    @abstractmethod
    def find_product_by_name(self, household_id: int, name: str) -> ProductSummary | None:
        raise NotImplementedError

    @abstractmethod
    def create_product(
        self, household_id: int, name: str, default_unit_code: str, is_food: bool
    ) -> ProductSummary:
        raise NotImplementedError

    @abstractmethod
    def rename_product(self, household_id: int, product_id: int, name: str) -> ProductSummary:
        raise NotImplementedError

    @abstractmethod
    def get_or_create_product(
        self, household_id: int, name: str, default_unit_code: str, is_food: bool
    ) -> ProductSummary:
        raise NotImplementedError
