from catalog.application.ports.catalog_repository import CatalogRepository
from catalog.domain.models import MeasurementUnitSummary


class ListMeasurementUnits:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    def execute(self) -> list[MeasurementUnitSummary]:
        return self._repository.list_measurement_units()
