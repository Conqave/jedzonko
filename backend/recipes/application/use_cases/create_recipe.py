from recipes.application.commands import RecipeInput
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.models import RecipeDetail


class CreateRecipe:
    def __init__(self, repository: RecipeRepository) -> None:
        self._repository = repository

    def execute(self, user_id: int, command: RecipeInput) -> RecipeDetail:
        return self._repository.create_recipe(command, user_id)
