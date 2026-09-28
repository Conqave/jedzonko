from django.urls import URLPattern, path

from households.presentation.product_views import (
    ProductTagDetailView,
    ProductTagListView,
    ProductListView,
    ProductTagOptionsView,
    TagAnalysisStartView,
    TagAnalysisStatusView,
)

urlpatterns: list[URLPattern] = [
    path("", ProductListView.as_view()),
    path("tags/", ProductTagOptionsView.as_view()),
    path("<int:product_id>/tags/", ProductTagListView.as_view()),
    path("tags/<int:tag_id>/", ProductTagDetailView.as_view()),
    path("<int:household_id>/tag-analysis/", TagAnalysisStartView.as_view()),
    path("tag-analysis/<str:job_id>/", TagAnalysisStatusView.as_view()),
]
