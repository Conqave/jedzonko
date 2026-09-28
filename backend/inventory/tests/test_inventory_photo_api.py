import io
from collections.abc import Iterator
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APIClient

from catalog.models import Product
from households.models import Household, HouseholdMembership
from inventory.models import InventoryItem
from inventory.presentation.photo_upload import MAX_PHOTO_BYTES

pytestmark = pytest.mark.django_db


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (200, 40, 40)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def media_root(tmp_path: Path) -> Iterator[Path]:
    with override_settings(MEDIA_ROOT=tmp_path):
        yield tmp_path


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def ala() -> User:
    return User.objects.create_user(username="ala", password="Ma-Kota-1234")


@pytest.fixture
def ola() -> User:
    return User.objects.create_user(username="ola", password="Ma-Psa-1234")


@pytest.fixture
def household(ala: User) -> Household:
    created = Household.objects.create(name="Dom Ali")
    HouseholdMembership.objects.create(household=created, user=ala)
    return created


@pytest.fixture
def item(household: Household) -> InventoryItem:
    product = Product.objects.create(
        household=household,
        name="Mąka pszenna",
        normalized_name="maka pszenna",
        default_unit_code="kg",
        is_food=True,
    )
    return InventoryItem.objects.create(product=product, unit_code="kg", quantity="2.000")


def test_member_uploads_replaces_and_deletes_a_photo(
    api_client: APIClient, ala: User, item: InventoryItem, media_root: Path
) -> None:
    api_client.force_login(ala)
    upload = SimpleUploadedFile("kot.png", _png_bytes(), content_type="image/png")

    response = api_client.put(
        f"/api/inventory/{item.pk}/photo/", {"photo": upload}, format="multipart"
    )

    assert response.status_code == 200
    photo_url = response.data["photo_url"]
    assert photo_url is not None
    assert photo_url.startswith("/media/inventory/")
    assert not photo_url.endswith("kot.png")
    stored = media_root / "inventory"
    assert len(list(stored.iterdir())) == 1

    replacement = SimpleUploadedFile("inny.png", _png_bytes(), content_type="image/png")
    replaced = api_client.put(
        f"/api/inventory/{item.pk}/photo/", {"photo": replacement}, format="multipart"
    )

    assert replaced.status_code == 200
    assert replaced.data["photo_url"] != photo_url
    assert len(list(stored.iterdir())) == 1

    removed = api_client.delete(f"/api/inventory/{item.pk}/photo/")

    assert removed.status_code == 200
    assert removed.data["photo_url"] is None
    assert list(stored.iterdir()) == []


def test_a_non_image_upload_is_rejected(
    api_client: APIClient, ala: User, item: InventoryItem
) -> None:
    api_client.force_login(ala)
    upload = SimpleUploadedFile("zlosliwy.png", b"not an image at all", content_type="image/png")

    response = api_client.put(
        f"/api/inventory/{item.pk}/photo/", {"photo": upload}, format="multipart"
    )

    assert response.status_code == 400
    assert response.data["code"] == "invalid_photo"


def test_an_unsupported_content_type_is_rejected(
    api_client: APIClient, ala: User, item: InventoryItem
) -> None:
    api_client.force_login(ala)
    upload = SimpleUploadedFile("lista.pdf", _png_bytes(), content_type="application/pdf")

    response = api_client.put(
        f"/api/inventory/{item.pk}/photo/", {"photo": upload}, format="multipart"
    )

    assert response.status_code == 400
    assert response.data["code"] == "unsupported_photo_type"


def test_an_oversized_upload_is_rejected(
    api_client: APIClient, ala: User, item: InventoryItem
) -> None:
    api_client.force_login(ala)
    upload = SimpleUploadedFile("duze.png", b"0" * (MAX_PHOTO_BYTES + 1), content_type="image/png")

    response = api_client.put(
        f"/api/inventory/{item.pk}/photo/", {"photo": upload}, format="multipart"
    )

    assert response.status_code == 400
    assert response.data["code"] == "photo_too_large"


def test_uploading_a_photo_is_denied_for_another_household(
    api_client: APIClient, ola: User, item: InventoryItem
) -> None:
    api_client.force_login(ola)
    upload = SimpleUploadedFile("kot.png", _png_bytes(), content_type="image/png")

    response = api_client.put(
        f"/api/inventory/{item.pk}/photo/", {"photo": upload}, format="multipart"
    )

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_deleting_a_photo_is_denied_for_another_household(
    api_client: APIClient, ala: User, ola: User, item: InventoryItem
) -> None:
    api_client.force_login(ala)
    upload = SimpleUploadedFile("kot.png", _png_bytes(), content_type="image/png")
    api_client.put(f"/api/inventory/{item.pk}/photo/", {"photo": upload}, format="multipart")
    api_client.force_login(ola)

    response = api_client.delete(f"/api/inventory/{item.pk}/photo/")

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_a_photo_url_is_not_readable_without_membership(
    api_client: APIClient, ala: User, ola: User, item: InventoryItem
) -> None:
    api_client.force_login(ala)
    upload = SimpleUploadedFile("kot.png", _png_bytes(), content_type="image/png")
    api_client.put(f"/api/inventory/{item.pk}/photo/", {"photo": upload}, format="multipart")
    api_client.force_login(ola)

    response = api_client.get("/api/inventory/", {"household_id": item.product.household_id})

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"
