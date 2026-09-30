from bs4 import BeautifulSoup, Tag

from recipes.application.errors import RecipeSourceContractError
from recipes.domain.external import ImportedExternalRecipe
from recipes.infrastructure.providers.ania_gotuje.ingredient_line import parse_ingredient_line
from recipes.infrastructure.providers.ania_gotuje.mapper import RECIPE_PAGE_BASE_URL

_RECIPE_TYPE = "https://schema.org/Recipe"


def read_recipe_page(html: str, reference: str) -> ImportedExternalRecipe:
    soup = BeautifulSoup(html, "html.parser")
    recipe = soup.find(attrs={"itemtype": _RECIPE_TYPE})
    if not isinstance(recipe, Tag):
        raise RecipeSourceContractError(f"Recipe page {reference!r} has no schema.org Recipe.")
    names = _read_property(recipe, "name")
    if len(names) != 1:
        raise RecipeSourceContractError(f"Recipe page {reference!r} has no single name.")
    texts = _read_property(recipe, "recipeIngredient")
    if not texts:
        raise RecipeSourceContractError(f"Recipe page {reference!r} lists no ingredients.")
    ingredients = tuple(parse_ingredient_line(text) for text in texts)
    image_source_url = _read_optional_property(recipe, "image", reference)
    yield_label = _read_optional_property(recipe, "recipeYield", reference)
    return ImportedExternalRecipe(
        reference=reference,
        name=names[0],
        source_url=f"{RECIPE_PAGE_BASE_URL}/{reference}",
        image_source_url=image_source_url,
        yield_label=yield_label,
        ingredients=ingredients,
    )


def _read_optional_property(recipe: Tag, name: str, reference: str) -> str | None:
    values = _read_property(recipe, name)
    if len(values) > 1:
        raise RecipeSourceContractError(f"Recipe page {reference!r} repeats {name!r}.")
    return values[0] if values else None


def _read_property(recipe: Tag, name: str) -> list[str]:
    values: list[str] = []
    for element in recipe.find_all(attrs={"itemprop": name}):
        owner = element.find_parent(attrs={"itemscope": True})
        if owner is not recipe:
            continue
        value = _read_value(element)
        if value:
            values.append(value)
    return values


def _read_value(element: Tag) -> str:
    if element.name == "meta":
        content = element.get("content")
        text = content if isinstance(content, str) else ""
    else:
        text = element.get_text(separator=" ", strip=True)
    return " ".join(text.split())
