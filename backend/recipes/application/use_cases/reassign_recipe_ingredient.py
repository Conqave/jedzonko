from recipes.application.ports.recipe_repository import RecipeRepository


class ReassignRecipeIngredient:

    def __init__(self, repository: RecipeRepository) -> None:
        self._repository = repository

    def execute(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        self._repository.reassign_ingredient(source_ingredient_id, target_ingredient_id)
