from abc import ABC, abstractmethod


class IngredientClassifier(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def find_matching_tags(self, product_name: str, tag_names: tuple[str, ...]) -> tuple[int, ...]:
        raise NotImplementedError
