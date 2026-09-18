from collections.abc import Iterator
from contextlib import contextmanager

import httpx
from django.conf import settings

from promotions.application.ports.promotion_source import PromotionSource
from promotions.infrastructure.providers.blix.provider import BlixProvider


@contextmanager
def open_promotion_source() -> Iterator[PromotionSource]:
    with httpx.Client(
        timeout=httpx.Timeout(settings.PROMOTIONS_HTTP_TIMEOUT_SECONDS),
        headers={"User-Agent": settings.PROMOTIONS_HTTP_USER_AGENT},
        follow_redirects=True,
    ) as client:
        yield BlixProvider(client)
