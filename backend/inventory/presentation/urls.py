from django.urls import URLPattern, path

from inventory.presentation.views import (
    InventoryCategoryDetailView,
    InventoryCategoryListView,
    InventoryItemCategoryView,
    InventoryItemMinimumView,
    InventoryItemPhotoView,
    InventoryItemView,
    InventoryListView,
)

urlpatterns: list[URLPattern] = [
    path("", InventoryListView.as_view()),
    path("categories/", InventoryCategoryListView.as_view()),
    path("categories/<int:category_id>/", InventoryCategoryDetailView.as_view()),
    path("<int:item_id>/", InventoryItemView.as_view()),
    path("<int:item_id>/category/", InventoryItemCategoryView.as_view()),
    path("<int:item_id>/minimum/", InventoryItemMinimumView.as_view()),
    path("<int:item_id>/photo/", InventoryItemPhotoView.as_view()),
]
