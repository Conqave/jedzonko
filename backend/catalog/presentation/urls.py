from django.urls import URLPattern, path

from catalog.presentation.views import (
    IngredientCaloriesView,
    IngredientDensityView,
    IngredientListView,
    IngredientPieceWeightView,
    MeasurementUnitListView,
    ProductDetailView,
    ProductIngredientAnalysisView,
    ProductIngredientConfirmationView,
    ProductIngredientDetailView,
    ProductIngredientListView,
    ProductIngredientRejectionView,
    ProductListView,
    ProductRejectedIngredientListView,
)

product_urlpatterns: list[URLPattern] = [
    path("", ProductListView.as_view()),
    path("<int:product_id>/", ProductDetailView.as_view()),
    path("<int:product_id>/ingredients/", ProductIngredientListView.as_view()),
    path(
        "<int:product_id>/ingredients/<int:ingredient_id>/",
        ProductIngredientDetailView.as_view(),
    ),
    path(
        "<int:product_id>/rejected-ingredients/",
        ProductRejectedIngredientListView.as_view(),
    ),
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
    path("<int:ingredient_id>/piece-weight/", IngredientPieceWeightView.as_view()),
    path("<int:ingredient_id>/density/", IngredientDensityView.as_view()),
]
unit_urlpatterns: list[URLPattern] = [path("", MeasurementUnitListView.as_view())]
