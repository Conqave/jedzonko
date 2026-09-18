from abc import ABC, abstractmethod

from catalog.domain.models import IngredientSummary, MeasurementUnitSummary


class CatalogRepository(ABC):
    @abstractmethod
    def list_ingredients(self, name_query: str | None) -> list[IngredientSummary]:
        raise NotImplementedError

    @abstractmethod
    def list_measurement_units(self) -> list[MeasurementUnitSummary]:
        raise NotImplementedError
