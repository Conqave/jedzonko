from datetime import date
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from promotions.application.ports.promotion_source import (
    PromotionSource,
    PromotionSourceUnavailable,
)
from promotions.domain.models import Leaflet, LeafletPage, PromotionOffer, Shop
from promotions.infrastructure.providers.blix.parser import BlixSearchParser


class BlixProvider(PromotionSource):
    base_url = "https://blix.pl"

    def __init__(self, client: httpx.Client) -> None:
        self._client = client
        self._search_parser = BlixSearchParser(self.base_url)

    def list_shops(self) -> list[Shop]:
        response = self._get(f"{self.base_url}/sklepy")
        soup = BeautifulSoup(response.text, "html.parser")
        shops: list[Shop] = []
        for anchor in soup.select("div.section-n__items.section-n__items--brands > a"):
            title = anchor.get("title")
            href = anchor.get("href")
            if isinstance(title, str) and title.strip() and isinstance(href, str) and href.strip():
                shops.append(Shop(name=title.strip(), url=urljoin(self.base_url, href)))
        return shops

    def list_leaflets(self, shop_name: str) -> list[Leaflet]:
        slug = self._normalize_shop_name(shop_name)
        response = self._get(f"{self.base_url}/sklep/{slug}")
        soup = BeautifulSoup(response.text, "html.parser")
        result: list[Leaflet] = []
        for card in soup.select("div.leaflet.section-n__item"):
            brand_slug = card.get("data-brand-slug")
            if (
                isinstance(brand_slug, str)
                and brand_slug
                and brand_slug.casefold() != slug.casefold()
            ):
                continue
            anchor = card.select_one("a.leaflet__link[href]")
            if anchor is None:
                continue
            href = anchor.get("href")
            if not isinstance(href, str) or not href:
                continue
            leaflet_url = urljoin(self.base_url, href)
            provider_id = self._extract_leaflet_id(leaflet_url)
            if provider_id is None:
                continue
            image = anchor.select_one("picture img")
            cover_url = None
            if image is not None:
                source = image.get("src") or image.get("data-src")
                if isinstance(source, str) and source:
                    cover_url = urljoin(self.base_url, source)
            label = anchor.select_one(".leaflet__availability .availability__label")
            validity_label = label.get_text(strip=True) if label is not None else None
            result.append(
                Leaflet(
                    provider_id=provider_id,
                    shop_name=shop_name,
                    url=leaflet_url,
                    cover_url=cover_url,
                    validity_label=validity_label,
                    downloaded_on=date.today(),
                )
            )
        return result

    def list_leaflet_pages(self, leaflet_provider_id: str) -> list[LeafletPage]:
        response = self._get(f"{self.base_url}/gazetka/{leaflet_provider_id}")
        soup = BeautifulSoup(response.text, "html.parser")
        needle = f"/{leaflet_provider_id}/"
        urls: list[str] = []
        for element in soup.select(
            f'img[src*="{needle}"], img[data-src*="{needle}"], source[srcset*="{needle}"]'
        ):
            candidates: list[str] = []
            for attr in ("data-src", "src"):
                value = element.get(attr)
                if isinstance(value, str) and value:
                    candidates.append(value)
            srcset = element.get("srcset")
            if isinstance(srcset, str):
                candidates.extend(
                    part.strip().split()[0] for part in srcset.split(",") if part.strip()
                )
            for candidate in candidates:
                absolute = urljoin(str(response.url), candidate)
                if needle in absolute and absolute not in urls:
                    urls.append(absolute)
        return [LeafletPage(leaflet_provider_id=leaflet_provider_id, image_url=url) for url in urls]

    def search_promotions(self, query: str) -> list[PromotionOffer]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")

        response = self._get(
            f"{self.base_url}/szukaj/",
            params={"szukaj": normalized_query},
        )
        return self._search_parser.parse(response.text)

    def _get(self, url: str, params: dict[str, str] | None = None) -> httpx.Response:
        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise PromotionSourceUnavailable(f"Blix request failed: {url}") from error
        return response

    @staticmethod
    def _normalize_shop_name(shop_name: str) -> str:
        normalized = shop_name.strip().casefold().replace("é", "e")
        return normalized.replace(" ", "-")

    @staticmethod
    def _extract_leaflet_id(url: str) -> str | None:
        parts = [part for part in url.rstrip("/").split("/") if part]
        for part in reversed(parts):
            if part.isdigit():
                return part
        return None
