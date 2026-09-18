from catalog.application.ports.catalog_repository import CatalogRepository
from catalog.application.use_cases.list_ingredients import ListIngredients
from catalog.application.use_cases.list_measurement_units import ListMeasurementUnits
from catalog.infrastructure.django_catalog_repository import DjangoCatalogRepository


def build_catalog_repository() -> CatalogRepository:
    return DjangoCatalogRepository()


def build_list_ingredients() -> ListIngredients:
    return ListIngredients(build_catalog_repository())


def build_list_measurement_units() -> ListMeasurementUnits:
    return ListMeasurementUnits(build_catalog_repository())
