from abc import ABC, abstractmethod


class IngredientNames(ABC):
    @abstractmethod
    def find_names(self, ingredient_ids: set[int]) -> dict[int, str]:
        raise NotImplementedError
