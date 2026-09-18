from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.models import RecipeSummary


class ListRecipes:
    def __init__(self, repository: RecipeRepository) -> None:
        self._repository = repository

    def execute(self) -> list[RecipeSummary]:
        return self._repository.list_recipes()
