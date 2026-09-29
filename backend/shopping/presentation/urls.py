from django.urls import URLPattern, path

from shopping.presentation.views import (
    MinimumStockSynchronizationView,
    ShoppingItemDetailView,
    ShoppingItemProductView,
    ShoppingItemPurchaseView,
    ShoppingItemRestoreView,
    ShoppingListDetailView,
    ShoppingListExternalRecipeItemsView,
    ShoppingListItemListView,
    ShoppingListListView,
    ShoppingListPromotionSplitView,
    ShoppingListPurchaseView,
    ShoppingListRecipeItemsView,
)

urlpatterns: list[URLPattern] = [
    path("lists/", ShoppingListListView.as_view()),
    path("lists/<int:list_id>/", ShoppingListDetailView.as_view()),
    path("lists/<int:list_id>/items/", ShoppingListItemListView.as_view()),
    path("lists/<int:list_id>/recipe-items/", ShoppingListRecipeItemsView.as_view()),
    path("lists/<int:list_id>/purchase/", ShoppingListPurchaseView.as_view()),
    path("lists/<int:list_id>/promotion-split/", ShoppingListPromotionSplitView.as_view()),
    path(
        "lists/<int:list_id>/external-recipe-items/",
        ShoppingListExternalRecipeItemsView.as_view(),
    ),
    path("households/<int:household_id>/minimum-stock/", MinimumStockSynchronizationView.as_view()),
    path("items/<int:item_id>/", ShoppingItemDetailView.as_view()),
    path("items/<int:item_id>/product/", ShoppingItemProductView.as_view()),
    path("items/<int:item_id>/purchase/", ShoppingItemPurchaseView.as_view()),
    path("items/<int:item_id>/restore/", ShoppingItemRestoreView.as_view()),
]
