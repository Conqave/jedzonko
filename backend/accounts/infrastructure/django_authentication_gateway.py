from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpRequest

from accounts.application.dto import AuthenticatedUser
from accounts.application.ports.authentication_gateway import AuthenticationGateway
from promotions.application.permissions import VIEW_PROMOTIONS_PERMISSION


class DjangoAuthenticationGateway(AuthenticationGateway):
    def __init__(self, request: HttpRequest) -> None:
        self._request = request

    def find_user_by_credentials(self, username: str, password: str) -> AuthenticatedUser | None:
        user = authenticate(self._request, username=username, password=password)
        if user is None:
            return None
        if not isinstance(user, User):
            raise TypeError("Authentication backend returned an unsupported user model.")
        return self._to_dto(user)

    def start_session(self, user: AuthenticatedUser) -> None:
        login(self._request, User.objects.get(pk=user.id))

    def end_session(self) -> None:
        logout(self._request)

    def get_session_user(self) -> AuthenticatedUser | None:
        user = self._request.user
        if not isinstance(user, User):
            return None
        return self._to_dto(user)

    @staticmethod
    def _to_dto(user: User) -> AuthenticatedUser:
        return AuthenticatedUser(
            id=user.pk,
            username=user.get_username(),
            is_staff=user.is_staff,
            can_view_promotions=user.has_perm(VIEW_PROMOTIONS_PERMISSION),
        )
