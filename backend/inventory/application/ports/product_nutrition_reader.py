from abc import ABC, abstractmethod

from shared.item_calories import SubjectNutrition


class ProductNutritionReader(ABC):
    @abstractmethod
    def find_product_nutrition(
        self, household_id: int, product_ids: set[int]
    ) -> dict[int, SubjectNutrition]:
        raise NotImplementedError
