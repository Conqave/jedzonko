from catalog.application.ports.catalog_repository import CatalogRepository
from catalog.domain.measurement import MeasurementDimension
from catalog.domain.models import IngredientSummary, MeasurementUnitSummary
from catalog.models import Ingredient, MeasurementUnit


class DjangoCatalogRepository(CatalogRepository):
    def list_ingredients(self, name_query: str | None) -> list[IngredientSummary]:
        rows = Ingredient.objects.select_related("default_unit")
        if name_query is not None:
            rows = rows.filter(name__icontains=name_query)
        return [
            IngredientSummary(id=row.pk, name=row.name, default_unit_code=row.default_unit.code)
            for row in rows
        ]

    def list_measurement_units(self) -> list[MeasurementUnitSummary]:
        return [
            MeasurementUnitSummary(
                code=row.code, name=row.name, dimension=MeasurementDimension(row.dimension)
            )
            for row in MeasurementUnit.objects.all()
        ]
