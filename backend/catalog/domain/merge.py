from catalog.domain.product_ingredient import ProductIngredient, ProductIngredientStatus

_STRENGTH = {
    ProductIngredientStatus.REJECTED: 0,
    ProductIngredientStatus.PROPOSED: 1,
    ProductIngredientStatus.CONFIRMED: 2,
}


def surviving_link(target: ProductIngredient, source: ProductIngredient) -> ProductIngredient:
    if _STRENGTH[source.status] > _STRENGTH[target.status]:
        return ProductIngredient(
            product_id=source.product_id,
            ingredient_id=target.ingredient_id,
            status=source.status,
            source=source.source,
            model_name=source.model_name,
            proposed_at=source.proposed_at,
            decided_at=source.decided_at,
        )
    return target
