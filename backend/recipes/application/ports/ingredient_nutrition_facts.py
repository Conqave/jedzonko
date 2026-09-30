from abc import ABC, abstractmethod

from shared.nutrition import NutritionFacts


class IngredientNutritionFacts(ABC):
    @abstractmethod
    def find_nutrition_facts(self, ingredient_ids: set[int]) -> dict[int, NutritionFacts]:
        raise NotImplementedError
