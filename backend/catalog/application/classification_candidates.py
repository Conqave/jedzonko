from catalog.domain.classification import ProductClassification
from catalog.domain.ingredient import Ingredient


def find_undecided_tags(
    tags: list[Ingredient], classification: ProductClassification
) -> tuple[Ingredient, ...]:
    return tuple(tag for tag in tags if classification.find(tag.id) is None)
