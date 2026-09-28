from django.urls import URLPattern, path

from accounts.presentation.views import CsrfTokenView, CurrentUserView, LoginView, LogoutView, ChangePasswordView

urlpatterns: list[URLPattern] = [
    path("csrf/", CsrfTokenView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", CurrentUserView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
]
