from xml.etree import ElementTree

from recipes.application.errors import RecipeSourceContractError
from recipes.infrastructure.providers.ania_gotuje.mapper import RECIPE_PAGE_BASE_URL

_SITEMAP_NAMESPACE = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_RECIPE_PREFIX = f"{RECIPE_PAGE_BASE_URL}/"


def read_recipe_references(xml: str) -> tuple[str, ...]:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as error:
        raise RecipeSourceContractError("Sitemap is not valid XML.") from error
    if root.tag != f"{_SITEMAP_NAMESPACE}urlset":
        raise RecipeSourceContractError(f"Sitemap root is {root.tag!r}, not a url set.")
    references: list[str] = []
    for location in root.iter(f"{_SITEMAP_NAMESPACE}loc"):
        url = (location.text or "").strip()
        if not url.startswith(_RECIPE_PREFIX):
            continue
        reference = url.removeprefix(_RECIPE_PREFIX).strip("/")
        if reference and "/" not in reference and reference not in references:
            references.append(reference)
    return tuple(references)
