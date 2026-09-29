from abc import ABC, abstractmethod

from catalog.domain.classification import ProductClassification
from catalog.domain.product_ingredient import ProductIngredient


class ProductClassificationRepository(ABC):
    @abstractmethod
    def find(self, product_id: int) -> ProductClassification | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, changes: tuple[ProductIngredient, ...]) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_confirmed(self, household_id: int) -> dict[int, tuple[int, ...]]:
        raise NotImplementedError

    @abstractmethod
    def list_links_to(self, ingredient_id: int) -> list[ProductIngredient]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, product_id: int, ingredient_id: int) -> None:
        raise NotImplementedError
