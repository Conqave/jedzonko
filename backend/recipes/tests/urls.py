from django.urls import URLResolver, include, path

urlpatterns: list[URLResolver] = [path("api/recipes/", include("recipes.presentation.urls"))]
