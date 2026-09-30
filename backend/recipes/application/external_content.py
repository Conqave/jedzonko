from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipeContent


def read_external_content(
    catalog: ExternalRecipeCatalog, source: RecipeSource, reference: str
) -> ExternalRecipeContent:
    stored = catalog.find_content(reference)
    if stored is not None:
        return stored
    recipe = source.get_recipe(reference)
    return ExternalRecipeContent(
        yield_label=recipe.summary.yield_label, ingredients=recipe.ingredients
    )
