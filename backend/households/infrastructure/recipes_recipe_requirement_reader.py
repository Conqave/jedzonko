from households.application.ports.recipe_requirement_reader import RecipeRequirementReader
from households.domain.ingredient_requirement import IngredientRequirement
from recipes.composition import build_list_recipe_requirement_names


class RecipesRecipeRequirementReader(RecipeRequirementReader):
    def list_requirements(self) -> list[IngredientRequirement]:
        return [
            IngredientRequirement(name=entry.name, normalized_name=entry.normalized_name)
            for entry in build_list_recipe_requirement_names().execute()
        ]
