from django.urls import URLPattern, path

from households.presentation.product_views import ProductListView

urlpatterns: list[URLPattern] = [path("", ProductListView.as_view())]
