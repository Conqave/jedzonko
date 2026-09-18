from django.urls import URLPattern, path

from catalog.presentation.views import IngredientListView, MeasurementUnitListView

urlpatterns: list[URLPattern] = [
    path("ingredients/", IngredientListView.as_view()),
    path("units/", MeasurementUnitListView.as_view()),
]
