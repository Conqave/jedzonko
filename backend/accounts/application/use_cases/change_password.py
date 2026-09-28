from accounts.application.errors import NotAuthenticatedError, WrongCurrentPasswordError
from accounts.application.ports.authentication_gateway import AuthenticationGateway


class ChangePassword:
    def __init__(self, gateway: AuthenticationGateway) -> None:
        self._gateway = gateway

    def execute(self, current_password: str, new_password: str) -> None:
        user = self._gateway.get_session_user()
        if user is None:
            raise NotAuthenticatedError
        if not self._gateway.check_password(user.id, current_password):
            raise WrongCurrentPasswordError
        self._gateway.set_password(user.id, new_password)
