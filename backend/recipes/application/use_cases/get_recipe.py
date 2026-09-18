from recipes.application.errors import RecipeNotFoundError
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.models import RecipeDetail


class GetRecipe:
    def __init__(self, repository: RecipeRepository) -> None:
        self._repository = repository

    def execute(self, recipe_id: int) -> RecipeDetail:
        recipe = self._repository.find_recipe(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError
        return recipe
