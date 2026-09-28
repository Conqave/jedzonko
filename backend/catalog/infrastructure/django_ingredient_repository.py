from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import (
    Ingredient,
    IngredientName,
    IngredientNameKind,
    IngredientNameSource,
)
from catalog.domain.names import CatalogName
from catalog.models import Ingredient as IngredientRow
from catalog.models import IngredientName as IngredientNameRow

ALIAS = IngredientNameKind.ALIAS.value
CANONICAL = IngredientNameKind.CANONICAL.value


class DjangoIngredientRepository(IngredientRepository):
    def find(self, ingredient_id: int) -> Ingredient | None:
        row = IngredientRow.objects.filter(pk=ingredient_id).first()
        return None if row is None else _to_ingredient(row)

    def find_many(self, ingredient_ids: set[int]) -> dict[int, Ingredient]:
        rows = IngredientRow.objects.filter(pk__in=ingredient_ids)
        return {row.pk: _to_ingredient(row) for row in rows}

    def find_by_normalized_name(self, normalized_name: str) -> Ingredient | None:
        row = IngredientRow.objects.filter(names__normalized_name=normalized_name).first()
        return None if row is None else _to_ingredient(row)

    def find_by_normalized_names(self, normalized_names: set[str]) -> dict[str, Ingredient]:
        rows = IngredientNameRow.objects.filter(
            normalized_name__in=normalized_names
        ).select_related("ingredient")
        return {row.normalized_name: _to_ingredient(row.ingredient) for row in rows}

    def search(self, normalized_query: str, limit: int) -> list[Ingredient]:
        rows = (
            IngredientRow.objects.filter(names__normalized_name__contains=normalized_query)
            .distinct()
            .order_by("name")[:limit]
        )
        return [_to_ingredient(row) for row in rows]

    def list_names(self) -> list[IngredientName]:
        return [_to_name(row) for row in IngredientNameRow.objects.all()]

    def create(self, name: CatalogName, source: IngredientNameSource) -> Ingredient:
        row = IngredientRow.objects.create(name=name.name)
        IngredientNameRow.objects.create(
            ingredient=row,
            name=name.name,
            normalized_name=name.normalized_name,
            kind=CANONICAL,
            source=source.value,
        )
        return _to_ingredient(row)

    def add_name(
        self,
        ingredient_id: int,
        name: CatalogName,
        kind: IngredientNameKind,
        source: IngredientNameSource,
    ) -> IngredientName:
        row = IngredientNameRow.objects.create(
            ingredient_id=ingredient_id,
            name=name.name,
            normalized_name=name.normalized_name,
            kind=kind.value,
            source=source.value,
        )
        return _to_name(row)

    def move_names_as_aliases(self, source_id: int, target_id: int) -> None:
        IngredientNameRow.objects.filter(ingredient_id=source_id).update(
            ingredient_id=target_id, kind=ALIAS
        )

    def delete(self, ingredient_id: int) -> None:
        IngredientRow.objects.filter(pk=ingredient_id).delete()


def _to_ingredient(row: IngredientRow) -> Ingredient:
    return Ingredient(id=row.pk, name=row.name)


def _to_name(row: IngredientNameRow) -> IngredientName:
    return IngredientName(
        ingredient_id=row.ingredient_id,
        name=row.name,
        normalized_name=row.normalized_name,
        kind=IngredientNameKind(row.kind),
        source=IngredientNameSource(row.source),
    )
