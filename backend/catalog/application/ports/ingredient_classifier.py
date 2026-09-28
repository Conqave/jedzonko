from abc import ABC, abstractmethod


class IngredientClassifier(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def find_matching_ingredient(
        self, product_name: str, ingredient_names: tuple[str, ...]
    ) -> int | None:
        raise NotImplementedError
