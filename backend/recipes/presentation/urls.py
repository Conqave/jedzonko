from django.urls import URLPattern, path

from recipes.presentation.external_views import (
    ExternalRecipeDetailView,
    ExternalRecipeIngredientMatchingView,
    ExternalRecipeListView,
    ExternalRecipeMissingItemListView,
    ExternalRecipeSuggestionListView,
)
from recipes.presentation.views import (
    RecipeCategoryListView,
    RecipeDetailView,
    RecipeListView,
    RecipeMissingItemListView,
    RecipePreparationView,
    RecipeSuggestionListView,
)

urlpatterns: list[URLPattern] = [
    path("", RecipeListView.as_view()),
    path("categories/", RecipeCategoryListView.as_view()),
    path("suggestions/", RecipeSuggestionListView.as_view()),
    path("external/", ExternalRecipeListView.as_view()),
    path("external/suggestions/", ExternalRecipeSuggestionListView.as_view()),
    path("external/<slug:reference>/", ExternalRecipeDetailView.as_view()),
    path("external/<slug:reference>/missing-items/", ExternalRecipeMissingItemListView.as_view()),
    path(
        "external/<slug:reference>/ingredient-matching/",
        ExternalRecipeIngredientMatchingView.as_view(),
    ),
    path("<int:recipe_id>/", RecipeDetailView.as_view()),
    path("<int:recipe_id>/missing-items/", RecipeMissingItemListView.as_view()),
    path("<int:recipe_id>/confirm-preparation/", RecipePreparationView.as_view()),
]
