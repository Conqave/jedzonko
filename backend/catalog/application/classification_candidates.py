from catalog.domain.classification import ProductClassification
from catalog.domain.ingredient import Ingredient, IngredientName, IngredientNameKind


def find_undecided_tags(
    names: list[IngredientName], classification: ProductClassification
) -> tuple[Ingredient, ...]:
    canonical = [name for name in names if name.kind is IngredientNameKind.CANONICAL]
    undecided = [name for name in canonical if classification.find(name.ingredient_id) is None]
    ordered = sorted(undecided, key=lambda name: name.normalized_name)
    return tuple(Ingredient(id=name.ingredient_id, name=name.name) for name in ordered)
