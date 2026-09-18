from accounts.application.ports.authentication_gateway import AuthenticationGateway


class LogoutUser:
    def __init__(self, gateway: AuthenticationGateway) -> None:
        self._gateway = gateway

    def execute(self) -> None:
        self._gateway.end_session()
