from django.urls import URLPattern, path

from catalog.presentation.views import (
    IngredientCaloriesView,
    IngredientListView,
    MeasurementUnitListView,
    ProductDetailView,
    ProductIngredientAnalysisView,
    ProductIngredientConfirmationView,
    ProductIngredientListView,
    ProductIngredientRejectionView,
    ProductListView,
)

product_urlpatterns: list[URLPattern] = [
    path("", ProductListView.as_view()),
    path("<int:product_id>/", ProductDetailView.as_view()),
    path("<int:product_id>/ingredients/", ProductIngredientListView.as_view()),
    path("<int:product_id>/ingredient-analysis/", ProductIngredientAnalysisView.as_view()),
    path(
        "<int:product_id>/ingredients/<int:ingredient_id>/confirmation/",
        ProductIngredientConfirmationView.as_view(),
    ),
    path(
        "<int:product_id>/ingredients/<int:ingredient_id>/rejection/",
        ProductIngredientRejectionView.as_view(),
    ),
]
ingredient_urlpatterns: list[URLPattern] = [
    path("", IngredientListView.as_view()),
    path("<int:ingredient_id>/calories/", IngredientCaloriesView.as_view()),
]
unit_urlpatterns: list[URLPattern] = [path("", MeasurementUnitListView.as_view())]
