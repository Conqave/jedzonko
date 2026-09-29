from django.db import models

from recipes.application.commands import RecipeInput, ResolvedIngredient
from recipes.application.errors import (
    MeasurementUnitNotFoundError,
    RecipeCategoryNotFoundError,
    RecipeNotFoundError,
)
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.models import (
    RecipeCategory,
    RecipeDetail,
    RecipeIngredientDetail,
    RecipeRequirement,
    RecipeStepDetail,
    RecipeSummary,
)
from recipes.models import Recipe
from recipes.models import RecipeCategory as RecipeCategoryRow
from recipes.models import RecipeIngredient, RecipeStep, RecipeTag
from shared.measurement import MeasurementUnit, Quantity
from shared.measurement_units import find_measurement_unit


class DjangoRecipeRepository(RecipeRepository):
    def list_recipes(self) -> list[RecipeSummary]:
        rows = Recipe.objects.select_related("category", "created_by").prefetch_related("tags")
        return [self._to_summary(row) for row in rows]

    def list_categories(self) -> list[RecipeCategory]:
        rows = RecipeCategoryRow.objects.order_by("name")
        return [_to_category(row) for row in rows]

    def find_recipe(self, recipe_id: int) -> RecipeDetail | None:
        row = self._detail_queryset().filter(pk=recipe_id).first()
        return None if row is None else self._to_detail(row)

    def list_requirements(self, recipe_id: int) -> list[RecipeRequirement]:
        rows = RecipeIngredient.objects.filter(recipe_id=recipe_id)
        return [self._to_requirement(row) for row in rows]

    def list_requirements_by_recipe(self) -> dict[int, list[RecipeRequirement]]:
        grouped: dict[int, list[RecipeRequirement]] = {}
        for row in RecipeIngredient.objects.all():
            requirement = self._to_requirement(row)
            grouped.setdefault(row.recipe_id, []).append(requirement)
        return grouped

    def create_recipe(
        self,
        command: RecipeInput,
        ingredients: tuple[ResolvedIngredient, ...],
        created_by_user_id: int,
    ) -> RecipeDetail:
        category = self._resolve_category(command.category_id)
        recipe = Recipe.objects.create(
            name=command.name,
            description=command.description,
            servings=command.servings,
            preparation_time_minutes=command.preparation_time_minutes,
            cooking_time_minutes=command.cooking_time_minutes,
            difficulty=command.difficulty.value,
            category=category,
            created_by_id=created_by_user_id,
        )
        self._replace_children(recipe, command, ingredients)
        stored = self.find_recipe(recipe.pk)
        if stored is None:
            raise RecipeNotFoundError
        return stored

    def update_recipe(
        self, recipe_id: int, command: RecipeInput, ingredients: tuple[ResolvedIngredient, ...]
    ) -> RecipeDetail:
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
        self._replace_children(recipe, command, ingredients)
        stored = self.find_recipe(recipe_id)
        if stored is None:
            raise RecipeNotFoundError
        return stored

    def reassign_ingredient(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        RecipeIngredient.objects.filter(ingredient_id=source_ingredient_id).update(
            ingredient_id=target_ingredient_id
        )

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
    def _resolve_category(category_id: int | None) -> RecipeCategoryRow | None:
        if category_id is None:
            return None
        category = RecipeCategoryRow.objects.filter(pk=category_id).first()
        if category is None:
            raise RecipeCategoryNotFoundError
        return category

    @staticmethod
    def _replace_children(
        recipe: Recipe, command: RecipeInput, ingredients: tuple[ResolvedIngredient, ...]
    ) -> None:
        tags = [RecipeTag.objects.get_or_create(name=name)[0] for name in command.tag_names]
        recipe.tags.set(tags)
        RecipeStep.objects.bulk_create(
            [
                RecipeStep(recipe=recipe, position=step.position, text=step.text)
                for step in command.steps
            ]
        )
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=line.ingredient_id,
                    name=line.name,
                    normalized_name=line.normalized_name,
                    unit_code=line.unit_code,
                    quantity=line.quantity,
                )
                for line in ingredients
            ]
        )

    @staticmethod
    def _to_unit(unit_code: str) -> MeasurementUnit:
        unit = find_measurement_unit(unit_code)
        if unit is None:
            raise MeasurementUnitNotFoundError
        return unit

    @classmethod
    def _to_requirement(cls, row: RecipeIngredient) -> RecipeRequirement:
        unit = cls._to_unit(row.unit_code)
        quantity = Quantity(amount=row.quantity, unit=unit)
        return RecipeRequirement(name=row.name, ingredient_id=row.ingredient_id, quantity=quantity)

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
            category=None if row.category is None else _to_category(row.category),
            tag_names=tuple(tag.name for tag in row.tags.all()),
            image_url=row.image.url if row.image else None,
            author_username=row.created_by.get_username(),
        )

    @classmethod
    def _to_detail(cls, row: Recipe) -> RecipeDetail:
        summary = cls._to_summary(row)
        return RecipeDetail(
            summary=summary,
            steps=tuple(
                RecipeStepDetail(position=step.position, text=step.text) for step in row.steps.all()
            ),
            ingredients=tuple(
                RecipeIngredientDetail(
                    name=item.name,
                    ingredient_id=item.ingredient_id,
                    quantity=item.quantity,
                    unit_code=item.unit_code,
                )
                for item in row.ingredients.all()
            ),
        )


def _to_category(row: RecipeCategoryRow) -> RecipeCategory:
    return RecipeCategory(id=row.pk, name=row.name)
