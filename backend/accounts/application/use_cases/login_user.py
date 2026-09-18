from accounts.application.dto import AuthenticatedUser
from accounts.application.errors import InvalidCredentialsError
from accounts.application.ports.authentication_gateway import AuthenticationGateway


class LoginUser:
    def __init__(self, gateway: AuthenticationGateway) -> None:
        self._gateway = gateway

    def execute(self, username: str, password: str) -> AuthenticatedUser:
        user = self._gateway.find_user_by_credentials(username, password)
        if user is None:
            raise InvalidCredentialsError
        self._gateway.start_session(user)
        return user
