from recipes.application.commands import RecipeInput
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.models import RecipeDetail


class UpdateRecipe:
    def __init__(self, repository: RecipeRepository) -> None:
        self._repository = repository

    def execute(self, recipe_id: int, command: RecipeInput) -> RecipeDetail:
        return self._repository.update_recipe(recipe_id, command)
