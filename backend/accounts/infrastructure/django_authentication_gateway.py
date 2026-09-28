from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.http import HttpRequest

from accounts.application.dto import AuthenticatedUser
from accounts.application.ports.authentication_gateway import AuthenticationGateway
from accounts.application.ports.promotion_access import PromotionAccess


class DjangoAuthenticationGateway(AuthenticationGateway):
    def __init__(self, request: HttpRequest, promotion_access: PromotionAccess) -> None:
        self._request = request
        self._promotion_access = promotion_access

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

    def check_password(self, user_id: int, password: str) -> bool:
        user = User.objects.get(pk=user_id)
        return user.check_password(password)

    def set_password(self, user_id: int, password: str) -> None:
        user = User.objects.get(pk=user_id)
        user.set_password(password)
        user.save(update_fields=["password"])
        update_session_auth_hash(self._request, user)

    def _to_dto(self, user: User) -> AuthenticatedUser:
        can_view_promotions = self._promotion_access.can_view_promotions(user.pk)
        return AuthenticatedUser(
            id=user.pk,
            username=user.get_username(),
            is_staff=user.is_staff,
            can_view_promotions=can_view_promotions,
        )
