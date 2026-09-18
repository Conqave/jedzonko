import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from promotions.application.ports.promotion_source import PromotionSourceContractError
from promotions.domain.models import PromotionOffer


@dataclass(frozen=True, slots=True)
class _LeafletMetadata:
    shop_name: str
    shop_slug: str


class BlixSearchParser:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def parse(self, html: str) -> list[PromotionOffer]:
        soup = BeautifulSoup(html, "html.parser")
        if "window.offers" not in html and self._is_no_results_page(soup):
            return []
        offers = self._load_offers(html)
        leaflets = self._load_leaflet_metadata(soup)
        return [self._map_offer(offer, leaflets) for offer in offers]

    @staticmethod
    def _is_no_results_page(soup: BeautifulSoup) -> bool:
        for heading in soup.select("h1"):
            if heading.get_text(strip=True).casefold().startswith("brak wyników"):
                return True
        return False

    def _load_offers(self, html: str) -> list[Mapping[object, object]]:
        marker = "window.offers"
        marker_index = html.find(marker)
        if marker_index < 0:
            raise PromotionSourceContractError("Blix response does not contain window.offers")

        array_start = html.find("[", marker_index)
        if array_start < 0:
            raise PromotionSourceContractError("Blix window.offers assignment is malformed")

        array_end = self._find_json_array_end(html, array_start)
        payload = json.loads(html[array_start:array_end])
        if not isinstance(payload, list):
            raise PromotionSourceContractError("Blix window.offers is not a list")

        result: list[Mapping[object, object]] = []
        for item in payload:
            if not isinstance(item, dict):
                raise PromotionSourceContractError("Blix offer entry is not an object")
            result.append(item)
        return result

    @staticmethod
    def _find_json_array_end(text: str, start: int) -> int:
        depth = 0
        in_string = False
        escaped = False

        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return index + 1

        raise PromotionSourceContractError("Blix window.offers JSON array is not closed")

    def _load_leaflet_metadata(self, soup: BeautifulSoup) -> dict[int, _LeafletMetadata]:
        result: dict[int, _LeafletMetadata] = {}

        for element in soup.select("[data-leaflet-id][data-brand-name][data-brand-slug]"):
            leaflet_id_text = element.get("data-leaflet-id")
            shop_name = element.get("data-brand-name")
            shop_slug = element.get("data-brand-slug")

            if not isinstance(leaflet_id_text, str):
                continue
            if not isinstance(shop_name, str) or not shop_name.strip():
                continue
            if not isinstance(shop_slug, str) or not shop_slug.strip():
                continue

            try:
                leaflet_id = int(leaflet_id_text)
            except ValueError as error:
                raise PromotionSourceContractError(
                    f"Blix leaflet id is not numeric: {leaflet_id_text}"
                ) from error

            result[leaflet_id] = _LeafletMetadata(
                shop_name=shop_name.strip(),
                shop_slug=shop_slug.strip(),
            )

        return result

    def _map_offer(
        self,
        offer: Mapping[object, object],
        leaflets: dict[int, _LeafletMetadata],
    ) -> PromotionOffer:
        leaflet_id = self._required_int(offer, "leafletId")
        metadata = leaflets.get(leaflet_id)
        if metadata is None:
            raise PromotionSourceContractError(
                f"Blix offer references unknown leaflet id: {leaflet_id}"
            )

        page_number = self._required_int(offer, "pageNumber")
        price_cents = self._optional_int(offer, "price")
        valid_from = self._required_date(offer, "dateStart")
        valid_until = self._required_date(offer, "dateEnd")

        shop_url = urljoin(self._base_url + "/", f"sklep/{metadata.shop_slug}/")
        leaflet_url = urljoin(
            self._base_url + "/",
            f"sklep/{metadata.shop_slug}/gazetka/{leaflet_id}/?pageNumber={page_number}",
        )

        return PromotionOffer(
            provider_offer_id=self._optional_str(offer, "hash"),
            name=self._required_str(offer, "name"),
            shop_name=metadata.shop_name,
            shop_url=shop_url,
            image_url=self._required_str(offer, "image"),
            product_brand_name=self._optional_str(offer, "brandName"),
            price=None if price_cents is None else Decimal(price_cents) / Decimal(100),
            leaflet_provider_id=str(leaflet_id),
            leaflet_url=leaflet_url,
            page_number=page_number,
            valid_from=valid_from,
            valid_until=valid_until,
        )

    @staticmethod
    def _required_str(mapping: Mapping[object, object], key: str) -> str:
        value = mapping[key]
        if not isinstance(value, str) or not value.strip():
            raise PromotionSourceContractError(f"Blix field {key} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _optional_str(mapping: Mapping[object, object], key: str) -> str | None:
        value = mapping[key]
        if value is None:
            return None
        if not isinstance(value, str):
            raise PromotionSourceContractError(f"Blix field {key} must be a string or null")
        return value.strip() or None

    @staticmethod
    def _optional_int(mapping: Mapping[object, object], key: str) -> int | None:
        value = mapping[key]
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise PromotionSourceContractError(f"Blix field {key} must be an integer or null")
        return value

    @staticmethod
    def _required_int(mapping: Mapping[object, object], key: str) -> int:
        value = mapping[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise PromotionSourceContractError(f"Blix field {key} must be an integer")
        return value

    @classmethod
    def _required_date(cls, mapping: Mapping[object, object], key: str) -> date:
        value = mapping[key]
        if not isinstance(value, dict):
            raise PromotionSourceContractError(f"Blix field {key} must be an object")
        date_text = cls._required_str(value, "date")
        try:
            return datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S.%f").date()
        except ValueError as error:
            raise PromotionSourceContractError(
                f"Blix field {key}.date has unsupported format: {date_text}"
            ) from error
