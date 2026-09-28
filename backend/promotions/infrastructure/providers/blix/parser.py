from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from promotions.application.errors import PromotionSourceContractError


@dataclass(frozen=True, slots=True)
class BlixLeafletHit:
    shop_name: str
    shop_slug: str
    leaflet_id: int
    leaflet_url: str
    page_number: int


class BlixSearchParser:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def parse(self, html: str) -> list[BlixLeafletHit]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.section-n__items--leaflets div.leaflet.section-n__item")
        if not cards:
            if self._is_no_results_page(soup):
                return []
            raise PromotionSourceContractError("Blix search response contains no leaflet hit list")

        hits: list[BlixLeafletHit] = []
        seen_urls: list[str] = []
        for card in cards:
            hit = self._map_card(card)
            if hit.leaflet_url in seen_urls:
                continue
            seen_urls.append(hit.leaflet_url)
            hits.append(hit)
        return hits

    @staticmethod
    def _is_no_results_page(soup: BeautifulSoup) -> bool:
        for heading in soup.select("h1"):
            if heading.get_text(strip=True).casefold().startswith("brak wyników"):
                return True
        return False

    def _map_card(self, card: Tag) -> BlixLeafletHit:
        shop_name = self._required_attribute(card, "data-brand-name")
        shop_slug = self._required_attribute(card, "data-brand-slug")
        leaflet_id = self._required_int_attribute(card, "data-leaflet-id")

        anchor = card.select_one("a.leaflet__link[href]")
        if anchor is None:
            raise PromotionSourceContractError("Blix leaflet hit has no leaflet link")
        href = self._required_attribute(anchor, "href")
        leaflet_url = urljoin(self._base_url + "/", href)
        page_number = self._read_page_number(leaflet_url)

        return BlixLeafletHit(
            shop_name=shop_name,
            shop_slug=shop_slug.casefold(),
            leaflet_id=leaflet_id,
            leaflet_url=leaflet_url,
            page_number=page_number,
        )

    @staticmethod
    def _required_attribute(element: Tag, name: str) -> str:
        value = element.get(name)
        if not isinstance(value, str) or not value.strip():
            raise PromotionSourceContractError(f"Blix leaflet hit is missing {name}")
        return value.strip()

    @classmethod
    def _required_int_attribute(cls, element: Tag, name: str) -> int:
        value = cls._required_attribute(element, name)
        if not value.isdigit():
            raise PromotionSourceContractError(f"Blix leaflet hit {name} is not numeric: {value}")
        return int(value)

    @staticmethod
    def _read_page_number(leaflet_url: str) -> int:
        values = parse_qs(urlparse(leaflet_url).query).get("pageNumber", [])
        if len(values) != 1 or not values[0].isdigit():
            raise PromotionSourceContractError(
                f"Blix leaflet hit url has no page number: {leaflet_url}"
            )
        return int(values[0])
