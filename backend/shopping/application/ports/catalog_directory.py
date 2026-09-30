from abc import ABC, abstractmethod


class CatalogDirectory(ABC):

    @abstractmethod
    def is_household_product(self, household_id: int, product_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def has_ingredient(self, ingredient_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def find_ingredient_name(self, ingredient_id: int) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def find_only_product_of_ingredient(self, household_id: int, ingredient_id: int) -> int | None:
        raise NotImplementedError
