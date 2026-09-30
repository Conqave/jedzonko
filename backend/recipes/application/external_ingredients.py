from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipeIngredient


def read_external_ingredients(
    catalog: ExternalRecipeCatalog, source: RecipeSource, reference: str
) -> tuple[ExternalRecipeIngredient, ...]:
    stored = catalog.find_ingredients(reference)
    if stored is not None:
        return stored
    recipe = source.get_recipe(reference)
    return recipe.ingredients
