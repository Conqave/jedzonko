from accounts.application.dto import AuthenticatedUser
from accounts.application.errors import NotAuthenticatedError
from accounts.application.ports.authentication_gateway import AuthenticationGateway


class GetCurrentUser:
    def __init__(self, gateway: AuthenticationGateway) -> None:
        self._gateway = gateway

    def execute(self) -> AuthenticatedUser:
        user = self._gateway.get_session_user()
        if user is None:
            raise NotAuthenticatedError
        return user
