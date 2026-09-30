from recipes.application.ports.ingredient_names import IngredientNames
from recipes.application.ports.ingredient_nutrition_facts import IngredientNutritionFacts
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.listing import RecipeListing, list_ingredient_names
from recipes.domain.nutrition import list_tagged_ingredient_ids, summarize_nutrition


class ListRecipes:
    def __init__(
        self,
        repository: RecipeRepository,
        nutrition_facts: IngredientNutritionFacts,
        names: IngredientNames,
    ) -> None:
        self._repository = repository
        self._nutrition_facts = nutrition_facts
        self._names = names

    def execute(self) -> list[RecipeListing]:
        recipes = self._repository.list_recipes()
        requirements_by_recipe = self._repository.list_requirements_by_recipe()
        all_requirements = [
            requirement
            for requirements in requirements_by_recipe.values()
            for requirement in requirements
        ]
        ingredient_ids = list_tagged_ingredient_ids(all_requirements)
        facts = self._nutrition_facts.find_nutrition_facts(ingredient_ids)
        tag_names = self._names.find_names(ingredient_ids)
        listings: list[RecipeListing] = []
        for recipe in recipes:
            requirements = requirements_by_recipe.get(recipe.id, [])
            nutrition = summarize_nutrition(requirements, facts, recipe.servings)
            ingredient_names = list_ingredient_names(requirements, tag_names)
            listing = RecipeListing(
                summary=recipe, nutrition=nutrition, ingredient_names=ingredient_names
            )
            listings.append(listing)
        return listings
