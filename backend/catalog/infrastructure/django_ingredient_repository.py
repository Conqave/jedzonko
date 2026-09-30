from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.calories import TagCalories
from catalog.domain.conversions import Density, PieceWeight
from catalog.domain.ingredient import (
    Ingredient,
    IngredientName,
    IngredientNameKind,
    IngredientNameSource,
)
from catalog.domain.ingredient_search import IngredientNameMatch
from catalog.domain.names import CatalogName
from catalog.domain.provenance import FactSource, Provenance
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

    def find_name_matches(self, normalized_query: str) -> list[IngredientNameMatch]:
        rows = IngredientNameRow.objects.filter(
            normalized_name__contains=normalized_query
        ).select_related("ingredient")
        return [_to_name_match(row) for row in rows]

    def list_tags(self) -> list[Ingredient]:
        rows = (
            IngredientNameRow.objects.filter(kind=CANONICAL)
            .select_related("ingredient")
            .order_by("normalized_name")
        )
        return [_to_ingredient(row.ingredient) for row in rows]

    def save_calories(self, ingredient_id: int, calories: TagCalories | None) -> None:
        rows = IngredientRow.objects.filter(pk=ingredient_id)
        if calories is None:
            rows.update(kcal_per_100g=None, kcal_source=None, kcal_reference_url=None)
            return
        rows.update(
            kcal_per_100g=calories.kcal_per_100g,
            kcal_source=calories.provenance.source.value,
            kcal_reference_url=calories.provenance.reference_url,
        )

    def save_piece_weight(self, ingredient_id: int, piece_weight: PieceWeight | None) -> None:
        rows = IngredientRow.objects.filter(pk=ingredient_id)
        if piece_weight is None:
            rows.update(
                grams_per_piece=None, piece_weight_source=None, piece_weight_reference_url=None
            )
            return
        rows.update(
            grams_per_piece=piece_weight.grams_per_piece,
            piece_weight_source=piece_weight.provenance.source.value,
            piece_weight_reference_url=piece_weight.provenance.reference_url,
        )

    def save_density(self, ingredient_id: int, density: Density | None) -> None:
        rows = IngredientRow.objects.filter(pk=ingredient_id)
        if density is None:
            rows.update(grams_per_ml=None, density_source=None, density_reference_url=None)
            return
        rows.update(
            grams_per_ml=density.grams_per_ml,
            density_source=density.provenance.source.value,
            density_reference_url=density.provenance.reference_url,
        )

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

    def split_alias(self, normalized_name: str) -> Ingredient | None:
        alias = IngredientNameRow.objects.filter(
            normalized_name=normalized_name, kind=ALIAS
        ).first()
        if alias is None:
            return None
        row = IngredientRow.objects.create(name=alias.name)
        alias.ingredient = row
        alias.kind = CANONICAL
        alias.save(update_fields=["ingredient", "kind"])
        return _to_ingredient(row)

    def delete(self, ingredient_id: int) -> None:
        IngredientRow.objects.filter(pk=ingredient_id).delete()


def _to_ingredient(row: IngredientRow) -> Ingredient:
    calories = _to_calories(row)
    piece_weight = _to_piece_weight(row)
    density = _to_density(row)
    return Ingredient(
        id=row.pk, name=row.name, calories=calories, piece_weight=piece_weight, density=density
    )


def _to_calories(row: IngredientRow) -> TagCalories | None:
    if row.kcal_per_100g is None:
        return None
    provenance = _to_provenance(row.pk, row.kcal_source, row.kcal_reference_url)
    return TagCalories(kcal_per_100g=row.kcal_per_100g, provenance=provenance)


def _to_piece_weight(row: IngredientRow) -> PieceWeight | None:
    if row.grams_per_piece is None:
        return None
    provenance = _to_provenance(row.pk, row.piece_weight_source, row.piece_weight_reference_url)
    return PieceWeight(grams_per_piece=row.grams_per_piece, provenance=provenance)


def _to_density(row: IngredientRow) -> Density | None:
    if row.grams_per_ml is None:
        return None
    provenance = _to_provenance(row.pk, row.density_source, row.density_reference_url)
    return Density(grams_per_ml=row.grams_per_ml, provenance=provenance)


def _to_provenance(ingredient_id: int, source: str | None, reference_url: str | None) -> Provenance:
    if source is None:
        raise AssertionError(f"Ingredient {ingredient_id} has a value without a source.")
    fact_source = FactSource(source)
    return Provenance(source=fact_source, reference_url=reference_url)


def _to_name_match(row: IngredientNameRow) -> IngredientNameMatch:
    ingredient = _to_ingredient(row.ingredient)
    return IngredientNameMatch(ingredient=ingredient, normalized_name=row.normalized_name)


def _to_name(row: IngredientNameRow) -> IngredientName:
    return IngredientName(
        ingredient_id=row.ingredient_id,
        name=row.name,
        normalized_name=row.normalized_name,
        kind=IngredientNameKind(row.kind),
        source=IngredientNameSource(row.source),
    )
