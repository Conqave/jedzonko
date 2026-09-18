from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Ingredient, MeasurementUnit
from recipes.domain.difficulty import RecipeDifficulty


class RecipeCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RecipeTag(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    servings = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    preparation_time_minutes = models.PositiveSmallIntegerField()
    cooking_time_minutes = models.PositiveSmallIntegerField()
    difficulty = models.CharField(
        max_length=16, choices=[(item.value, item.name.title()) for item in RecipeDifficulty]
    )
    image = models.ImageField(upload_to="recipes/", null=True, blank=True)
    category = models.ForeignKey(
        RecipeCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recipes",
    )
    tags = models.ManyToManyField(RecipeTag, blank=True, related_name="recipes")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_recipes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["name"]), models.Index(fields=["category"])]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="steps")
    position = models.PositiveSmallIntegerField()
    text = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "position"], name="unique_recipe_step_position"
            )
        ]
        ordering = ["recipe_id", "position"]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="recipe_ingredients"
    )
    unit = models.ForeignKey(
        MeasurementUnit, on_delete=models.PROTECT, related_name="recipe_ingredients"
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(0)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_recipe_ingredient"
            )
        ]
        indexes = [models.Index(fields=["ingredient"])]
        ordering = ["recipe_id", "ingredient_id"]
