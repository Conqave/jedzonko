from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.models import RecipeCategory


class ListRecipeCategories:
    def __init__(self, repository: RecipeRepository) -> None:
        self._repository = repository

    def execute(self) -> list[RecipeCategory]:
        return self._repository.list_categories()
