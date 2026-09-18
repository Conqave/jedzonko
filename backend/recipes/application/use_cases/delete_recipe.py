from recipes.application.ports.recipe_repository import RecipeRepository


class DeleteRecipe:
    def __init__(self, repository: RecipeRepository) -> None:
        self._repository = repository

    def execute(self, recipe_id: int) -> None:
        self._repository.delete_recipe(recipe_id)
