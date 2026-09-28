from dataclasses import dataclass

from django.http import HttpRequest

from accounts.application.ports.promotion_access import PromotionAccess
from accounts.application.use_cases.change_password import ChangePassword
from accounts.application.use_cases.get_current_user import GetCurrentUser
from accounts.application.use_cases.login_user import LoginUser
from accounts.application.use_cases.logout_user import LogoutUser
from accounts.infrastructure.django_authentication_gateway import DjangoAuthenticationGateway


@dataclass(frozen=True, slots=True)
class AccountOperations:
    login_user: LoginUser
    logout_user: LogoutUser
    get_current_user: GetCurrentUser
    change_password: ChangePassword


@dataclass(frozen=True, slots=True)
class AccountsModule:
    promotion_access: PromotionAccess

    def for_request(self, request: HttpRequest) -> AccountOperations:
        gateway = DjangoAuthenticationGateway(request, self.promotion_access)
        return AccountOperations(
            login_user=LoginUser(gateway),
            logout_user=LogoutUser(gateway),
            get_current_user=GetCurrentUser(gateway),
            change_password=ChangePassword(gateway),
        )


def build_accounts(promotion_access: PromotionAccess) -> AccountsModule:
    return AccountsModule(promotion_access=promotion_access)
