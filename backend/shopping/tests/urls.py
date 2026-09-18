from django.urls import URLResolver, include, path

urlpatterns: list[URLResolver] = [path("api/shopping/", include("shopping.presentation.urls"))]
