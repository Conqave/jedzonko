from abc import ABC, abstractmethod
from decimal import Decimal


class IngredientCalories(ABC):
    @abstractmethod
    def find_kcal_per_100g(self, ingredient_ids: set[int]) -> dict[int, Decimal]:
        raise NotImplementedError
