import json
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from promotions.application.errors import (
    PromotionSourceContractError,
    PromotionSourceUnavailableError,
)
from promotions.application.ports.promotion_source import PromotionSource
from promotions.domain.models import PromotionOffer, Shop
from promotions.infrastructure.providers.blix.leaflet_parser import BlixLeafletParser
from promotions.infrastructure.providers.blix.parser import BlixLeafletHit, BlixSearchParser


class BlixProvider(PromotionSource):
    base_url = "https://blix.pl"

    def __init__(self, client: httpx.Client, search_leaflet_limit: int) -> None:
        if search_leaflet_limit < 1:
            raise ValueError("search_leaflet_limit must be at least 1")
        self._client = client
        self._search_leaflet_limit = search_leaflet_limit
        self._search_parser = BlixSearchParser(self.base_url)
        self._leaflet_parser = BlixLeafletParser(self.base_url)

    def list_shops(self) -> list[Shop]:
        response = self._get(f"{self.base_url}/sklepy")
        soup = BeautifulSoup(response.text, "html.parser")
        shops: list[Shop] = []
        for anchor in soup.select("div.section-n__items.section-n__items--brands > a"):
            title = anchor.get("title")
            href = anchor.get("href")
            if not isinstance(title, str) or not title.strip():
                continue
            if not isinstance(href, str) or not href.strip():
                continue
            url = urljoin(self.base_url, href.strip())
            slug = self._extract_shop_slug(url)
            if slug is None:
                continue
            shops.append(Shop(name=title.strip(), slug=slug, url=url))
        return shops

    def search_promotions(self, query: str, shop_slugs: tuple[str, ...]) -> list[PromotionOffer]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")

        response = self._get(f"{self.base_url}/szukaj/", params={"szukaj": normalized_query})
        hits = self._search_parser.parse(response.text)
        selected_hits = self._select_hits(hits, shop_slugs)

        offers: list[PromotionOffer] = []
        for hit in selected_hits:
            payload = self._get_leaflet_payload(hit)
            matching = self._leaflet_parser.parse_matching_offers(payload, hit, normalized_query)
            offers.extend(matching)
        return offers

    def _select_hits(
        self, hits: list[BlixLeafletHit], shop_slugs: tuple[str, ...]
    ) -> list[BlixLeafletHit]:
        if shop_slugs:
            hits = [hit for hit in hits if hit.shop_slug in shop_slugs]
        return hits[: self._search_leaflet_limit]

    def _get_leaflet_payload(self, hit: BlixLeafletHit) -> object:
        response = self._get(f"{self.base_url}/getleaflet/{hit.shop_slug}/{hit.leaflet_id}/")
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise PromotionSourceContractError(
                f"Blix leaflet response is not valid JSON: {hit.shop_slug}/{hit.leaflet_id}"
            ) from error

    def _get(self, url: str, params: dict[str, str] | None = None) -> httpx.Response:
        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise PromotionSourceUnavailableError(f"Blix request failed: {url}") from error
        return response

    @staticmethod
    def _extract_shop_slug(url: str) -> str | None:
        parts = [part for part in urlparse(url).path.split("/") if part]
        if len(parts) < 2 or parts[0] != "sklep":
            return None
        return parts[1].casefold()
