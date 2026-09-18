from django.urls import URLPattern, path

from recipes.presentation.views import (
    RecipeDetailView,
    RecipeListView,
    RecipeMissingItemListView,
    RecipePreparationView,
    RecipeSuggestionListView,
)

urlpatterns: list[URLPattern] = [
    path("", RecipeListView.as_view()),
    path("suggestions/", RecipeSuggestionListView.as_view()),
    path("<int:recipe_id>/", RecipeDetailView.as_view()),
    path("<int:recipe_id>/missing-items/", RecipeMissingItemListView.as_view()),
    path("<int:recipe_id>/confirm-preparation/", RecipePreparationView.as_view()),
]
