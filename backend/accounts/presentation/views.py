from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.application.dto import AuthenticatedUser
from accounts.application.errors import InvalidCredentialsError
from accounts.application.use_cases.get_current_user import GetCurrentUser
from accounts.application.use_cases.login_user import LoginUser
from accounts.application.use_cases.logout_user import LogoutUser
from accounts.infrastructure.django_authentication_gateway import DjangoAuthenticationGateway
from accounts.presentation.serializers import LoginSerializer


def _build_gateway(request: Request) -> DjangoAuthenticationGateway:
    return DjangoAuthenticationGateway(request._request)


def _represent(user: AuthenticatedUser) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "is_staff": user.is_staff,
        "can_view_promotions": user.can_view_promotions,
    }


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        use_case = LoginUser(_build_gateway(request))
        try:
            user = use_case.execute(
                serializer.validated_data["username"], serializer.validated_data["password"]
            )
        except InvalidCredentialsError:
            raise AuthenticationFailed(
                detail="Invalid username or password.", code="invalid_credentials"
            )
        return Response(_represent(user))


class LogoutView(APIView):
    def post(self, request: Request) -> Response:
        LogoutUser(_build_gateway(request)).execute()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    def get(self, request: Request) -> Response:
        user = GetCurrentUser(_build_gateway(request)).execute()
        return Response(_represent(user))
