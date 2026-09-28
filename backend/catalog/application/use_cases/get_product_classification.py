from dataclasses import dataclass

from catalog.application.errors import ProductNotFoundError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.domain.ingredient import Ingredient
from catalog.domain.product_ingredient import ProductIngredient
from shared.household_membership import HouseholdMembershipReader, require_membership


@dataclass(frozen=True, slots=True)
class ClassifiedLink:
    link: ProductIngredient
    ingredient: Ingredient


class GetProductClassification:
    def __init__(
        self,
        classifications: ProductClassificationRepository,
        ingredients: IngredientRepository,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._classifications = classifications
        self._ingredients = ingredients
        self._memberships = memberships

    def execute(self, user_id: int, product_id: int) -> list[ClassifiedLink]:
        classification = self._classifications.find(product_id)
        if classification is None:
            raise ProductNotFoundError
        require_membership(self._memberships, user_id, classification.household_id)
        ingredients = self._ingredients.find_many(
            {link.ingredient_id for link in classification.links}
        )
        return [
            ClassifiedLink(link=link, ingredient=ingredients[link.ingredient_id])
            for link in classification.links
        ]
