from catalog.domain.ingredient import IngredientName

MAX_CLASSIFICATION_CANDIDATES = 20


def select_classification_candidates(
    normalized_product_name: str, names: list[IngredientName]
) -> list[int]:
    product_words = set(normalized_product_name.split())
    overlap: dict[int, int] = {}
    for name in names:
        shared = len(product_words & set(name.normalized_name.split()))
        if shared:
            overlap[name.ingredient_id] = max(shared, overlap.get(name.ingredient_id, 0))
    ranked = sorted(overlap, key=lambda ingredient_id: (-overlap[ingredient_id], ingredient_id))
    return ranked[:MAX_CLASSIFICATION_CANDIDATES]
