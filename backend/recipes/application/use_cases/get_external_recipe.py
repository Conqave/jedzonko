from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipeDetail


class GetExternalRecipe:
    def __init__(self, source: RecipeSource) -> None:
        self._source = source

    def execute(self, reference: str) -> ExternalRecipeDetail:
        return self._source.get_recipe(reference)
