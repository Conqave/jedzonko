from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone

from catalog.domain.ingredient import IngredientNameSource
from catalog.models import Ingredient, Product
from config.composition import container
from households.models import Household
from recipes.models import Recipe, RecipeIngredient
from shared.text import normalize_text


def make_household(owner: User, name: str) -> Household:
    use_case = container().households.create_household
    summary = use_case.execute(name, owner.pk)
    return Household.objects.get(pk=summary.id)


def make_product(household: Household, name: str, default_unit_code: str) -> Product:
    return Product.objects.create(
        household=household,
        name=name,
        normalized_name=normalize_text(name),
        default_unit_code=default_unit_code,
        is_food=True,
    )


def make_ingredient(name: str) -> Ingredient:
    use_case = container().catalog.create_ingredient
    ingredient = use_case.execute(name, IngredientNameSource.MANUAL)
    return Ingredient.objects.get(pk=ingredient.id)


def confirm_ingredient(owner: User, product: Product, ingredient: Ingredient) -> None:
    use_case = container().catalog.confirm_product_ingredient
    now = timezone.now()
    use_case.execute(owner.pk, product.pk, ingredient.pk, now)


def add_recipe_line(recipe: Recipe, ingredient: Ingredient | None, name: str, grams: str) -> None:
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ingredient,
        name=name,
        normalized_name=normalize_text(name),
        unit_code="g",
        quantity=Decimal(grams),
    )
