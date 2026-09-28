from django.urls import URLPattern, path

from households.presentation.views import (
    DeletedHouseholdListView,
    HouseholdDetailView,
    HouseholdListView,
    HouseholdMemberDetailView,
    HouseholdMemberListView,
    HouseholdRestoreView,
)

urlpatterns: list[URLPattern] = [
    path("", HouseholdListView.as_view()),
    path("deleted/", DeletedHouseholdListView.as_view()),
    path("<int:household_id>/", HouseholdDetailView.as_view()),
    path("<int:household_id>/restore/", HouseholdRestoreView.as_view()),
    path("<int:household_id>/members/", HouseholdMemberListView.as_view()),
    path("<int:household_id>/members/<int:member_user_id>/", HouseholdMemberDetailView.as_view()),
]
