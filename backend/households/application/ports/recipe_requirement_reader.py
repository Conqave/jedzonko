from abc import ABC, abstractmethod

from households.domain.ingredient_requirement import IngredientRequirement


class RecipeRequirementReader(ABC):
    @abstractmethod
    def list_requirements(self) -> list[IngredientRequirement]:
        raise NotImplementedError
