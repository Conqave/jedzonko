import io
from uuid import uuid4

from django.core.files.uploadedfile import UploadedFile
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

from inventory.domain.photo import InventoryPhoto

MAX_PHOTO_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
EXTENSIONS_BY_FORMAT = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


class InventoryPhotoUpload:
    @classmethod
    def read(cls, uploaded: UploadedFile[bytes]) -> InventoryPhoto:
        if uploaded.size is None or uploaded.size > MAX_PHOTO_BYTES:
            raise ValidationError(detail="The photo is too large.", code="photo_too_large")
        if uploaded.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                detail="Unsupported photo content type.", code="unsupported_photo_type"
            )
        content = uploaded.read()
        image_format = cls._read_format(content)
        if image_format not in EXTENSIONS_BY_FORMAT:
            raise ValidationError(detail="The file is not an image.", code="invalid_photo")
        return InventoryPhoto(
            filename=f"{uuid4().hex}{EXTENSIONS_BY_FORMAT[image_format]}", content=content
        )

    @staticmethod
    def _read_format(content: bytes) -> str:
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
                return str(image.format)
        except UnidentifiedImageError, OSError, ValueError:
            raise ValidationError(detail="The file is not an image.", code="invalid_photo")
