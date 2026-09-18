from django.urls import URLPattern, path

from promotions.presentation.views import PromotionSearchView, StorePromotionCoverageView

urlpatterns: list[URLPattern] = [
    path("search/", PromotionSearchView.as_view()),
    path("store-coverage/", StorePromotionCoverageView.as_view()),
]
