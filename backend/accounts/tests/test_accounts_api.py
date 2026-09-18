import pytest
from django.contrib.auth.models import Permission, User
from rest_framework.test import APIClient

from promotions.application.permissions import VIEW_PROMOTIONS_PERMISSION

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def normal_user() -> User:
    return User.objects.create_user(username="ala", password="Ma-Kota-1234")


def _grant_promotion_access(user: User) -> None:
    app_label, codename = VIEW_PROMOTIONS_PERMISSION.split(".")
    user.user_permissions.add(
        Permission.objects.get(content_type__app_label=app_label, codename=codename)
    )


def test_csrf_endpoint_sets_cookie_for_anonymous_caller(api_client: APIClient) -> None:
    response = api_client.get("/api/accounts/csrf/")

    assert response.status_code == 204
    assert "csrftoken" in response.cookies


def test_login_returns_current_user(api_client: APIClient, normal_user: User) -> None:
    response = api_client.post(
        "/api/accounts/login/", {"username": "ala", "password": "Ma-Kota-1234"}, format="json"
    )

    assert response.status_code == 200
    assert response.data == {
        "id": normal_user.pk,
        "username": "ala",
        "is_staff": False,
        "can_view_promotions": False,
    }


def test_login_rejects_wrong_password(api_client: APIClient, normal_user: User) -> None:
    response = api_client.post(
        "/api/accounts/login/", {"username": "ala", "password": "nope"}, format="json"
    )

    assert response.status_code == 403
    assert response.data["code"] == "invalid_credentials"


def test_login_rejects_missing_fields(api_client: APIClient) -> None:
    response = api_client.post("/api/accounts/login/", {"username": "ala"}, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "invalid"


def test_current_user_is_denied_for_anonymous_caller(api_client: APIClient) -> None:
    response = api_client.get("/api/accounts/me/")

    assert response.status_code == 403
    assert response.data["code"] == "not_authenticated"


def test_logout_invalidates_session(api_client: APIClient, normal_user: User) -> None:
    api_client.post(
        "/api/accounts/login/", {"username": "ala", "password": "Ma-Kota-1234"}, format="json"
    )

    logout_response = api_client.post("/api/accounts/logout/")

    assert logout_response.status_code == 204
    assert api_client.get("/api/accounts/me/").status_code == 403


def test_new_user_has_no_promotion_access(api_client: APIClient, normal_user: User) -> None:
    api_client.force_login(normal_user)

    response = api_client.get("/api/accounts/me/")

    assert response.data["can_view_promotions"] is False


def test_granting_and_revoking_promotion_access_changes_current_user(
    api_client: APIClient, normal_user: User
) -> None:
    _grant_promotion_access(normal_user)
    api_client.force_login(User.objects.get(pk=normal_user.pk))

    assert api_client.get("/api/accounts/me/").data["can_view_promotions"] is True

    normal_user.user_permissions.clear()
    api_client.force_login(User.objects.get(pk=normal_user.pk))

    assert api_client.get("/api/accounts/me/").data["can_view_promotions"] is False
