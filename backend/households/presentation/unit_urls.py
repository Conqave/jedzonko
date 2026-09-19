from django.urls import URLPattern, path

from households.presentation.unit_views import MeasurementUnitListView

urlpatterns: list[URLPattern] = [path("", MeasurementUnitListView.as_view())]
