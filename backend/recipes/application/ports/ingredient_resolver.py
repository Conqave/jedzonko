from abc import ABC, abstractmethod


class IngredientResolver(ABC):
    @abstractmethod
    def find_ingredient_ids(self, names: tuple[str, ...]) -> dict[str, int]:
        raise NotImplementedError
