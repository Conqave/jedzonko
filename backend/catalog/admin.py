from django.contrib import admin

from catalog.models import Ingredient, MeasurementUnit


@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin[MeasurementUnit]):
    list_display = ["code", "name", "dimension", "factor_to_base"]
    list_filter = ["dimension"]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin[Ingredient]):
    list_display = ["name", "default_unit"]
    search_fields = ["name"]
