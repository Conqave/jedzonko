from django.conf import settings
from django.db import models
from django.db.models import Q

from recipes.domain.difficulty import RecipeDifficulty
from shared.enums import enum_choices, enum_values
from shared.measurement_units import MEASUREMENT_UNIT_CHOICES, MEASUREMENT_UNIT_CODES


class RecipeCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(name=""), name="recipe_category_name_not_empty"),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RecipeTag(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(name=""), name="recipe_tag_name_not_empty"),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    servings = models.PositiveSmallIntegerField()
    preparation_time_minutes = models.PositiveSmallIntegerField()
    cooking_time_minutes = models.PositiveSmallIntegerField()
    difficulty = models.CharField(max_length=16, choices=enum_choices(RecipeDifficulty))
    image = models.ImageField(upload_to="recipes/", null=True, blank=True)
    category = models.ForeignKey(
        RecipeCategory,
        null=True,
        blank=True,
        on_delete=models.DB_SET_NULL,
        related_name="recipes",
    )
    tags = models.ManyToManyField(
        RecipeTag, blank=True, related_name="recipes", through="RecipeTagging"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name="created_recipes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(name=""), name="recipe_name_not_empty"),
            models.CheckConstraint(condition=Q(servings__gte=1), name="recipe_serves_someone"),
            models.CheckConstraint(
                condition=Q(difficulty__in=enum_values(RecipeDifficulty)),
                name="recipe_difficulty_known",
            ),
        ]
        indexes = [models.Index(fields=["name"])]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RecipeTagging(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.DB_CASCADE)
    tag = models.ForeignKey(RecipeTag, on_delete=models.DB_CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["recipe", "tag"], name="unique_recipe_tagging"),
        ]


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.DB_CASCADE, related_name="steps")
    position = models.PositiveSmallIntegerField()
    text = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "position"], name="unique_recipe_step_position"
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1), name="recipe_step_position_from_one"
            ),
            models.CheckConstraint(condition=~Q(text=""), name="recipe_step_text_not_empty"),
        ]
        ordering = ["recipe_id", "position"]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.DB_CASCADE, related_name="ingredients")
    ingredient = models.ForeignKey(
        "catalog.Ingredient",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="recipe_lines",
    )
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=120)
    unit_code = models.CharField(max_length=16, choices=MEASUREMENT_UNIT_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "normalized_name"], name="unique_recipe_ingredient"
            ),
            models.CheckConstraint(condition=~Q(name=""), name="recipe_ingredient_name_not_empty"),
            models.CheckConstraint(
                condition=~Q(normalized_name=""),
                name="recipe_ingredient_normalized_name_not_empty",
            ),
            models.CheckConstraint(
                condition=Q(unit_code__in=MEASUREMENT_UNIT_CODES),
                name="recipe_ingredient_unit_known",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="recipe_ingredient_quantity_positive"
            ),
        ]
        ordering = ["recipe_id", "name"]

    def __str__(self) -> str:
        return self.name
