from abc import ABC, abstractmethod

from accounts.application.dto import AuthenticatedUser


class AuthenticationGateway(ABC):
    @abstractmethod
    def find_user_by_credentials(self, username: str, password: str) -> AuthenticatedUser | None:
        raise NotImplementedError

    @abstractmethod
    def start_session(self, user: AuthenticatedUser) -> None:
        raise NotImplementedError

    @abstractmethod
    def end_session(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_session_user(self) -> AuthenticatedUser | None:
        raise NotImplementedError

    @abstractmethod
    def check_password(self, user_id: int, password: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_password(self, user_id: int, password: str) -> None:
        raise NotImplementedError
