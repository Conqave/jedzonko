from datetime import datetime

from django.core.files.base import ContentFile
from django.db.models import Q

from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.domain.external import ExternalRecipeIngredient, ImportedExternalRecipe, RecipeImage
from recipes.models import ExternalRecipe, ExternalRecipeLine

_WITHOUT_IMAGE = Q(image__isnull=True) | Q(image="")


class DjangoExternalRecipeCatalog(ExternalRecipeCatalog):
    def __init__(self, source_name: str) -> None:
        self._source_name = source_name

    def list_references(self) -> frozenset[str]:
        rows = ExternalRecipe.objects.filter(source_name=self._source_name)
        references = rows.values_list("reference", flat=True)
        return frozenset(references)

    def list_missing_images(self) -> dict[str, str]:
        rows = ExternalRecipe.objects.filter(
            _WITHOUT_IMAGE, source_name=self._source_name, image_source_url__isnull=False
        )
        return {row.reference: row.image_source_url for row in rows if row.image_source_url}

    def find_ingredients(self, reference: str) -> tuple[ExternalRecipeIngredient, ...] | None:
        recipe = self._find_row(reference)
        if recipe is None:
            return None
        rows = ExternalRecipeLine.objects.filter(recipe=recipe).order_by("position")
        return tuple(_to_ingredient(row) for row in rows)

    def find_image_urls(self, references: tuple[str, ...]) -> dict[str, str]:
        rows = ExternalRecipe.objects.filter(
            source_name=self._source_name, reference__in=references
        ).exclude(_WITHOUT_IMAGE)
        return {row.reference: row.image.url for row in rows}

    def list_ingredient_texts(self) -> tuple[str, ...]:
        rows = ExternalRecipeLine.objects.filter(recipe__source_name=self._source_name)
        texts = rows.order_by("source_text").values_list("source_text", flat=True).distinct()
        return tuple(texts)

    def save_recipe(
        self, recipe: ImportedExternalRecipe, image: RecipeImage | None, fetched_at: datetime
    ) -> None:
        row = self._find_row(recipe.reference)
        if row is None:
            row = ExternalRecipe(source_name=self._source_name, reference=recipe.reference)
        keeps_image = image is None and row.image_source_url == recipe.image_source_url
        if row.image and not keeps_image:
            row.image.delete(save=False)
        row.name = recipe.name
        row.source_url = recipe.source_url
        row.image_source_url = recipe.image_source_url
        row.yield_label = recipe.yield_label
        row.fetched_at = fetched_at
        row.save()
        if image is not None:
            content = ContentFile(image.content)
            row.image.save(image.filename, content, save=True)
        ExternalRecipeLine.objects.filter(recipe=row).delete()
        lines = [
            ExternalRecipeLine(
                recipe=row,
                position=position,
                source_text=ingredient.source_text,
                name=ingredient.name,
                quantity=ingredient.quantity,
                unit_code=ingredient.unit_code,
            )
            for position, ingredient in enumerate(recipe.ingredients, start=1)
        ]
        ExternalRecipeLine.objects.bulk_create(lines)

    def save_image(self, reference: str, image: RecipeImage) -> None:
        row = self._find_row(reference)
        if row is None:
            raise ValueError(f"External recipe {reference!r} is not stored.")
        if row.image:
            row.image.delete(save=False)
        content = ContentFile(image.content)
        row.image.save(image.filename, content, save=True)

    def _find_row(self, reference: str) -> ExternalRecipe | None:
        return ExternalRecipe.objects.filter(
            source_name=self._source_name, reference=reference.strip()
        ).first()


def _to_ingredient(row: ExternalRecipeLine) -> ExternalRecipeIngredient:
    return ExternalRecipeIngredient(
        source_text=row.source_text,
        name=row.name,
        quantity=row.quantity,
        unit_code=row.unit_code,
    )
