import pytest

from accounts.application.dto import AuthenticatedUser
from accounts.application.errors import InvalidCredentialsError, NotAuthenticatedError
from accounts.application.ports.authentication_gateway import AuthenticationGateway
from accounts.application.use_cases.get_current_user import GetCurrentUser
from accounts.application.use_cases.login_user import LoginUser
from accounts.application.use_cases.logout_user import LogoutUser

KNOWN_USER = AuthenticatedUser(id=1, username="ala", is_staff=False, can_view_promotions=False)


class FakeAuthenticationGateway(AuthenticationGateway):
    def __init__(self, password: str) -> None:
        self._password = password
        self.session_user: AuthenticatedUser | None = None

    def find_user_by_credentials(self, username: str, password: str) -> AuthenticatedUser | None:
        if username == KNOWN_USER.username and password == self._password:
            return KNOWN_USER
        return None

    def start_session(self, user: AuthenticatedUser) -> None:
        self.session_user = user

    def end_session(self) -> None:
        self.session_user = None

    def get_session_user(self) -> AuthenticatedUser | None:
        return self.session_user


def test_login_user_starts_session_for_valid_credentials() -> None:
    gateway = FakeAuthenticationGateway("secret")

    user = LoginUser(gateway).execute("ala", "secret")

    assert user == KNOWN_USER
    assert gateway.session_user == KNOWN_USER


def test_login_user_rejects_invalid_credentials() -> None:
    gateway = FakeAuthenticationGateway("secret")

    with pytest.raises(InvalidCredentialsError):
        LoginUser(gateway).execute("ala", "wrong")

    assert gateway.session_user is None


def test_logout_user_clears_session() -> None:
    gateway = FakeAuthenticationGateway("secret")
    LoginUser(gateway).execute("ala", "secret")

    LogoutUser(gateway).execute()

    assert gateway.session_user is None


def test_get_current_user_requires_session() -> None:
    gateway = FakeAuthenticationGateway("secret")

    with pytest.raises(NotAuthenticatedError):
        GetCurrentUser(gateway).execute()
