from django.urls import URLPattern, path

from inventory.presentation.views import (
    InventoryCategoryListView,
    InventoryItemCategoryView,
    InventoryItemPhotoView,
    InventoryItemView,
    InventoryListView,
)

urlpatterns: list[URLPattern] = [
    path("", InventoryListView.as_view()),
    path("categories/", InventoryCategoryListView.as_view()),
    path("<int:item_id>/", InventoryItemView.as_view()),
    path("<int:item_id>/category/", InventoryItemCategoryView.as_view()),
    path("<int:item_id>/photo/", InventoryItemPhotoView.as_view()),
]
