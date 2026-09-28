from abc import ABC, abstractmethod


class IngredientMatcherError(Exception):
    pass


class IngredientMatcherUnavailable(IngredientMatcherError):
    pass


class IngredientMatcherContractError(IngredientMatcherError):
    pass


class IngredientMatcher(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def find_matching_product(
        self, ingredient_name: str, product_names: tuple[str, ...]
    ) -> int | None:
        raise NotImplementedError
