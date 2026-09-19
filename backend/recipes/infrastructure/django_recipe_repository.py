from django.db import models, transaction

from recipes.application.commands import RecipeInput
from recipes.application.errors import (
    DuplicateRecipeIngredientError,
    MeasurementUnitNotFoundError,
    RecipeCategoryNotFoundError,
    RecipeNotFoundError,
)
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.models import (
    RecipeDetail,
    RecipeIngredientDetail,
    RecipeRequirement,
    RecipeStepDetail,
    RecipeSummary,
)
from recipes.models import Recipe, RecipeCategory, RecipeIngredient, RecipeStep, RecipeTag
from shared.measurement import MeasurementUnit, Quantity
from shared.measurement_units import find_measurement_unit
from shared.text import normalize_text


class DjangoRecipeRepository(RecipeRepository):
    def list_recipes(self) -> list[RecipeSummary]:
        rows = Recipe.objects.select_related("category", "created_by").prefetch_related("tags")
        return [self._to_summary(row) for row in rows]

    def find_recipe(self, recipe_id: int) -> RecipeDetail | None:
        row = self._detail_queryset().filter(pk=recipe_id).first()
        return None if row is None else self._to_detail(row)

    def list_requirements(self, recipe_id: int) -> list[RecipeRequirement]:
        rows = RecipeIngredient.objects.filter(recipe_id=recipe_id)
        return [self._to_requirement(row) for row in rows]

    def list_requirements_by_recipe(self) -> dict[int, list[RecipeRequirement]]:
        grouped: dict[int, list[RecipeRequirement]] = {}
        for row in RecipeIngredient.objects.all():
            grouped.setdefault(row.recipe_id, []).append(self._to_requirement(row))
        return grouped

    def create_recipe(self, command: RecipeInput, created_by_user_id: int) -> RecipeDetail:
        with transaction.atomic():
            recipe = Recipe.objects.create(
                name=command.name,
                description=command.description,
                servings=command.servings,
                preparation_time_minutes=command.preparation_time_minutes,
                cooking_time_minutes=command.cooking_time_minutes,
                difficulty=command.difficulty.value,
                category=self._resolve_category(command.category_id),
                created_by_id=created_by_user_id,
            )
            self._replace_children(recipe, command)
        stored = self.find_recipe(recipe.pk)
        if stored is None:
            raise RecipeNotFoundError
        return stored

    def update_recipe(self, recipe_id: int, command: RecipeInput) -> RecipeDetail:
        with transaction.atomic():
            recipe = Recipe.objects.filter(pk=recipe_id).first()
            if recipe is None:
                raise RecipeNotFoundError
            recipe.name = command.name
            recipe.description = command.description
            recipe.servings = command.servings
            recipe.preparation_time_minutes = command.preparation_time_minutes
            recipe.cooking_time_minutes = command.cooking_time_minutes
            recipe.difficulty = command.difficulty.value
            recipe.category = self._resolve_category(command.category_id)
            recipe.save()
            recipe.steps.all().delete()
            recipe.ingredients.all().delete()
            self._replace_children(recipe, command)
        stored = self.find_recipe(recipe_id)
        if stored is None:
            raise RecipeNotFoundError
        return stored

    def delete_recipe(self, recipe_id: int) -> None:
        deleted, _ = Recipe.objects.filter(pk=recipe_id).delete()
        if deleted == 0:
            raise RecipeNotFoundError

    @staticmethod
    def _detail_queryset() -> models.QuerySet[Recipe]:
        return Recipe.objects.select_related("category", "created_by").prefetch_related(
            "tags", "steps", "ingredients"
        )

    @staticmethod
    def _resolve_category(category_id: int | None) -> RecipeCategory | None:
        if category_id is None:
            return None
        category = RecipeCategory.objects.filter(pk=category_id).first()
        if category is None:
            raise RecipeCategoryNotFoundError
        return category

    @classmethod
    def _replace_children(cls, recipe: Recipe, command: RecipeInput) -> None:
        tags = [RecipeTag.objects.get_or_create(name=name)[0] for name in command.tag_names]
        recipe.tags.set(tags)
        RecipeStep.objects.bulk_create(
            [
                RecipeStep(recipe=recipe, position=step.position, text=step.text)
                for step in command.steps
            ]
        )
        used_names: set[str] = set()
        for ingredient_input in command.ingredients:
            cls._to_unit(ingredient_input.unit_code)
            normalized_name = normalize_text(ingredient_input.name)
            if normalized_name in used_names:
                raise DuplicateRecipeIngredientError
            used_names.add(normalized_name)
            RecipeIngredient.objects.create(
                recipe=recipe,
                name=ingredient_input.name,
                normalized_name=normalized_name,
                unit_code=ingredient_input.unit_code,
                quantity=ingredient_input.quantity,
            )

    @staticmethod
    def _to_unit(unit_code: str) -> MeasurementUnit:
        unit = find_measurement_unit(unit_code)
        if unit is None:
            raise MeasurementUnitNotFoundError
        return unit

    @classmethod
    def _to_requirement(cls, row: RecipeIngredient) -> RecipeRequirement:
        return RecipeRequirement(
            name=row.name,
            normalized_name=row.normalized_name,
            quantity=Quantity(amount=row.quantity, unit=cls._to_unit(row.unit_code)),
        )

    @staticmethod
    def _to_summary(row: Recipe) -> RecipeSummary:
        return RecipeSummary(
            id=row.pk,
            name=row.name,
            description=row.description,
            servings=row.servings,
            preparation_time_minutes=row.preparation_time_minutes,
            cooking_time_minutes=row.cooking_time_minutes,
            difficulty=RecipeDifficulty(row.difficulty),
            category_name=None if row.category is None else row.category.name,
            tag_names=tuple(tag.name for tag in row.tags.all()),
            image_url=row.image.url if row.image else None,
            author_username=row.created_by.get_username(),
        )

    @classmethod
    def _to_detail(cls, row: Recipe) -> RecipeDetail:
        return RecipeDetail(
            summary=cls._to_summary(row),
            steps=tuple(
                RecipeStepDetail(position=step.position, text=step.text) for step in row.steps.all()
            ),
            ingredients=tuple(
                RecipeIngredientDetail(
                    name=item.name, quantity=item.quantity, unit_code=item.unit_code
                )
                for item in row.ingredients.all()
            ),
        )
