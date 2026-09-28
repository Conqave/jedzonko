from abc import ABC, abstractmethod

from catalog.domain.classification import ProductClassification
from catalog.domain.product_ingredient import ProductIngredient


class ProductClassificationRepository(ABC):
    @abstractmethod
    def find(self, product_id: int) -> ProductClassification | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, changes: tuple[ProductIngredient, ...]) -> None:
        """Store the changes in the given order, inserting or updating by (product, ingredient)."""
        raise NotImplementedError

    @abstractmethod
    def list_confirmed(self, household_id: int) -> dict[int, int]:
        """Map product id to its confirmed ingredient id."""
        raise NotImplementedError
