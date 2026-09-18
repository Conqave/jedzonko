from django.urls import URLPattern, path

from inventory.presentation.views import InventoryItemView, InventoryListView

urlpatterns: list[URLPattern] = [
    path("", InventoryListView.as_view()),
    path("<int:item_id>/", InventoryItemView.as_view()),
]
