from django.urls import URLPattern, path

from households.presentation.views import (
    HouseholdListView,
    HouseholdMemberDetailView,
    HouseholdMemberListView,
)

urlpatterns: list[URLPattern] = [
    path("", HouseholdListView.as_view()),
    path("<int:household_id>/members/", HouseholdMemberListView.as_view()),
    path("<int:household_id>/members/<int:member_user_id>/", HouseholdMemberDetailView.as_view()),
]
