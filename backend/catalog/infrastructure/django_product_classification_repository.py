from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.domain.classification import ProductClassification
from catalog.domain.product_ingredient import (
    ProductIngredient,
    ProductIngredientSource,
    ProductIngredientStatus,
)
from catalog.models import Product as ProductRow
from catalog.models import ProductIngredient as ProductIngredientRow

CONFIRMED = ProductIngredientStatus.CONFIRMED.value


class DjangoProductClassificationRepository(ProductClassificationRepository):
    def find(self, product_id: int) -> ProductClassification | None:
        household_id = (
            ProductRow.objects.filter(pk=product_id).values_list("household_id", flat=True).first()
        )
        if household_id is None:
            return None
        links = ProductIngredientRow.objects.filter(product_id=product_id)
        return ProductClassification(
            product_id=product_id,
            household_id=household_id,
            links=tuple(_to_link(row) for row in links),
        )

    def save(self, changes: tuple[ProductIngredient, ...]) -> None:
        for change in changes:
            ProductIngredientRow.objects.update_or_create(
                product_id=change.product_id,
                ingredient_id=change.ingredient_id,
                defaults={
                    "status": change.status.value,
                    "source": change.source.value,
                    "model_name": change.model_name,
                    "proposed_at": change.proposed_at,
                    "decided_at": change.decided_at,
                },
            )

    def list_confirmed(self, household_id: int) -> dict[int, int]:
        rows = ProductIngredientRow.objects.filter(
            product__household_id=household_id, status=CONFIRMED
        ).values_list("product_id", "ingredient_id")
        return dict(rows)

    def list_links_to(self, ingredient_id: int) -> list[ProductIngredient]:
        rows = ProductIngredientRow.objects.filter(ingredient_id=ingredient_id)
        return [_to_link(row) for row in rows]

    def delete(self, product_id: int, ingredient_id: int) -> None:
        ProductIngredientRow.objects.filter(
            product_id=product_id, ingredient_id=ingredient_id
        ).delete()


def _to_link(row: ProductIngredientRow) -> ProductIngredient:
    return ProductIngredient(
        product_id=row.product_id,
        ingredient_id=row.ingredient_id,
        status=ProductIngredientStatus(row.status),
        source=ProductIngredientSource(row.source),
        model_name=row.model_name,
        proposed_at=row.proposed_at,
        decided_at=row.decided_at,
    )
