from django.urls import URLPattern, path

from promotions.presentation.views import (
    FavouriteShopsView,
    PromotionSearchView,
    PromotionShopsView,
    StorePromotionCoverageView,
)

urlpatterns: list[URLPattern] = [
    path("shops/", PromotionShopsView.as_view()),
    path("favourite-shops/", FavouriteShopsView.as_view()),
    path("search/", PromotionSearchView.as_view()),
    path("store-coverage/", StorePromotionCoverageView.as_view()),
]
