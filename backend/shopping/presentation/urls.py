from django.urls import URLPattern, path

from shopping.presentation.views import (
    MinimumStockSynchronizationView,
    RecipeShoppingItemListView,
    ShoppingItemDetailView,
    ShoppingItemPurchaseView,
    PurchasedShoppingItemRestoreView,
    ShoppingListItemListView,
    ShoppingListListView,
    ShoppingListDeleteView,
)

urlpatterns: list[URLPattern] = [
    path("lists/", ShoppingListListView.as_view()),
    path("lists/<int:list_id>/", ShoppingListDeleteView.as_view()),
    path("lists/<int:list_id>/items/", ShoppingListItemListView.as_view()),
    path("lists/<int:list_id>/items/from-recipe/", RecipeShoppingItemListView.as_view()),
    path(
        "lists/<int:list_id>/synchronize-minimum-stock/",
        MinimumStockSynchronizationView.as_view(),
    ),
    path("items/<int:item_id>/buy/", ShoppingItemPurchaseView.as_view()),
    path("purchased-items/<int:item_id>/restore/", PurchasedShoppingItemRestoreView.as_view()),
    path("items/<int:item_id>/", ShoppingItemDetailView.as_view()),
]
