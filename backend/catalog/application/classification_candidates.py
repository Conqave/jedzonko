from catalog.domain.candidate_selection import select_classification_candidates
from catalog.domain.classification import ProductClassification
from catalog.domain.ingredient import IngredientName
from catalog.domain.names import CatalogName


def find_undecided_candidate_ids(
    product_name: str, names: list[IngredientName], classification: ProductClassification
) -> list[int]:
    normalized_name = CatalogName.parse(product_name).normalized_name
    candidate_ids = select_classification_candidates(normalized_name, names)
    return [
        ingredient_id
        for ingredient_id in candidate_ids
        if classification.find(ingredient_id) is None
    ]
