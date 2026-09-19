from abc import ABC, abstractmethod


class ProductResolver(ABC):
    @abstractmethod
    def resolve_product_id(self, household_id: int, name: str, default_unit_code: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def is_household_product(self, household_id: int, product_id: int) -> bool:
        raise NotImplementedError
