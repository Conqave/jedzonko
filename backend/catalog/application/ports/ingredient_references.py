from abc import ABC, abstractmethod


class IngredientReferences(ABC):

    @abstractmethod
    def reassign(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        raise NotImplementedError
