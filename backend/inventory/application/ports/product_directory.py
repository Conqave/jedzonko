from abc import ABC, abstractmethod


class ProductDirectory(ABC):
    @abstractmethod
    def is_household_product(self, household_id: int, product_id: int) -> bool:
        raise NotImplementedError
