from dataclasses import replace

from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipeDetail, with_local_image


class GetExternalRecipe:
    def __init__(self, catalog: ExternalRecipeCatalog, source: RecipeSource) -> None:
        self._catalog = catalog
        self._source = source

    def execute(self, reference: str) -> ExternalRecipeDetail:
        recipe = self._source.get_recipe(reference)
        local_image_urls = self._catalog.find_image_urls((recipe.summary.reference,))
        summary = with_local_image(recipe.summary, local_image_urls)
        return replace(recipe, summary=summary)
