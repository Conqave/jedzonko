from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.composition import AccountOperations
from accounts.presentation.serializers import (
    AuthenticatedUserSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
)
from config.composition import container


def _operations(request: Request) -> AccountOperations:
    accounts = container().accounts
    return accounts.for_request(request._request)


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        payload = LoginSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        operations = _operations(request)
        user = operations.login_user.execute(
            payload.validated_data["username"], payload.validated_data["password"]
        )
        serializer = AuthenticatedUserSerializer(user)
        return Response(serializer.data)


class LogoutView(APIView):
    def post(self, request: Request) -> Response:
        operations = _operations(request)
        operations.logout_user.execute()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    def get(self, request: Request) -> Response:
        operations = _operations(request)
        user = operations.get_current_user.execute()
        serializer = AuthenticatedUserSerializer(user)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    def post(self, request: Request) -> Response:
        payload = ChangePasswordSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        operations = _operations(request)
        operations.change_password.execute(
            payload.validated_data["current_password"], payload.validated_data["new_password"]
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
