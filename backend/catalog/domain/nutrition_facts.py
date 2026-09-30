from catalog.domain.ingredient import Ingredient
from catalog.domain.product import ProductIdentity, ProductPackage
from shared.item_calories import SubjectNutrition, TagGap
from shared.measurement import Quantity
from shared.measurement_units import find_measurement_unit
from shared.nutrition import NutritionFacts


def to_nutrition_facts(ingredient: Ingredient) -> NutritionFacts:
    calories = ingredient.calories
    piece_weight = ingredient.piece_weight
    density = ingredient.density
    return NutritionFacts(
        kcal_per_100g=None if calories is None else calories.kcal_per_100g,
        grams_per_piece=None if piece_weight is None else piece_weight.grams_per_piece,
        grams_per_ml=None if density is None else density.grams_per_ml,
    )


def to_ingredient_nutrition(ingredient: Ingredient) -> SubjectNutrition:
    facts = to_nutrition_facts(ingredient)
    return SubjectNutrition(facts=facts, package=None)


def find_product_nutrition(
    identity: ProductIdentity, ingredients: dict[int, Ingredient]
) -> SubjectNutrition:
    package = _to_package_quantity(identity.package)
    if not identity.tags:
        return SubjectNutrition(facts=TagGap.NO_TAG, package=package)
    if len(identity.tags) > 1:
        return SubjectNutrition(facts=TagGap.SEVERAL_TAGS, package=package)
    tag = identity.tags[0]
    ingredient = ingredients[tag.ingredient_id]
    facts = to_nutrition_facts(ingredient)
    return SubjectNutrition(facts=facts, package=package)


def _to_package_quantity(package: ProductPackage | None) -> Quantity | None:
    if package is None:
        return None
    unit = find_measurement_unit(package.unit_code)
    if unit is None:
        raise AssertionError(f"A package in the unknown unit {package.unit_code!r} was stored.")
    return Quantity(amount=package.quantity, unit=unit)
