from decimal import Decimal

from recipes.application.use_cases.list_recipes import ListRecipes
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.domain.nutrition import UncountedIngredient
from recipes.tests.factories import EGGS, FLOUR, GRAM, PIECE, make_requirement
from recipes.tests.fakes import (
    FakeIngredientNames,
    FakeIngredientNutritionFacts,
    FakeRecipeRepository,
)
from shared.nutrition import NutritionFacts, UncountedReason

PANCAKES = 1
OMELETTE = 2
TOAST = 3
FACTS = {
    FLOUR: NutritionFacts(kcal_per_100g=Decimal("364"), grams_per_piece=None, grams_per_ml=None),
    EGGS: NutritionFacts(
        kcal_per_100g=Decimal("143"), grams_per_piece=Decimal("60"), grams_per_ml=None
    ),
}
TAG_NAMES = {FLOUR: "mąka pszenna", EGGS: "jajko"}


def _recipe(recipe_id: int, name: str, servings: int) -> RecipeDetail:
    summary = RecipeSummary(
        id=recipe_id,
        name=name,
        description="",
        servings=servings,
        preparation_time_minutes=5,
        cooking_time_minutes=10,
        difficulty=RecipeDifficulty.EASY,
        category=None,
        tag_names=(),
        image_url=None,
        author_username=None,
    )
    return RecipeDetail(summary=summary, steps=(), ingredients=())


def _repository() -> FakeRecipeRepository:
    recipes = [
        _recipe(PANCAKES, "naleśniki", 2),
        _recipe(OMELETTE, "omlet", 1),
        _recipe(TOAST, "grzanki", 1),
    ]
    requirements = {
        PANCAKES: [
            make_requirement("mąka", "200", GRAM, FLOUR),
            make_requirement("jajka", "2", PIECE, EGGS),
        ],
        OMELETTE: [
            make_requirement("jajka", "3", PIECE, EGGS),
            make_requirement("szczypiorek", "10", GRAM, None),
        ],
    }
    return FakeRecipeRepository(recipes, requirements)


def test_the_list_summarizes_every_recipe_from_one_batch_of_reads() -> None:
    repository = _repository()
    nutrition_facts = FakeIngredientNutritionFacts(FACTS)
    names = FakeIngredientNames(TAG_NAMES)

    listings = ListRecipes(repository, nutrition_facts, names).execute()

    assert repository.requirement_query_count == 1
    assert nutrition_facts.asked == [{FLOUR, EGGS}]
    assert names.asked == [{FLOUR, EGGS}]
    assert [listing.summary.name for listing in listings] == ["naleśniki", "omlet", "grzanki"]


def test_each_listed_recipe_carries_its_calories_per_serving() -> None:
    listings = ListRecipes(
        _repository(), FakeIngredientNutritionFacts(FACTS), FakeIngredientNames(TAG_NAMES)
    ).execute()

    pancakes, omelette, toast = (listing.nutrition for listing in listings)
    assert pancakes.total_kcal == Decimal("899.60")
    assert pancakes.kcal_per_serving == Decimal("449.80")
    assert pancakes.has_estimates is True
    assert omelette.uncounted_ingredients == (
        UncountedIngredient(name="szczypiorek", reason=UncountedReason.NO_CALORIES),
    )
    assert toast.total_kcal == Decimal(0)
    assert toast.uncounted_ingredients == ()


def test_each_listed_recipe_names_its_ingredients_and_their_tags() -> None:
    listings = ListRecipes(
        _repository(), FakeIngredientNutritionFacts(FACTS), FakeIngredientNames(TAG_NAMES)
    ).execute()

    names = [listing.ingredient_names for listing in listings]
    assert names == [
        ("jajka", "jajko", "mąka", "mąka pszenna"),
        ("jajka", "jajko", "szczypiorek"),
        (),
    ]
