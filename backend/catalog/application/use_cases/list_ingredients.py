from catalog.application.ports.catalog_repository import CatalogRepository
from catalog.domain.models import IngredientSummary


class ListIngredients:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    def execute(self, name_query: str | None) -> list[IngredientSummary]:
        return self._repository.list_ingredients(name_query)
