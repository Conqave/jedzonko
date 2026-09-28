from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from promotions.application.ports.promotion_source import PromotionSourceContractError
from promotions.domain.matching import matches_query
from promotions.domain.models import PromotionOffer
from promotions.infrastructure.providers.blix.parser import BlixLeafletHit

_WARSAW = ZoneInfo("Europe/Warsaw")


class BlixLeafletParser:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def parse_matching_offers(
        self, payload: object, hit: BlixLeafletHit, query: str
    ) -> list[PromotionOffer]:
        if not isinstance(payload, dict):
            raise PromotionSourceContractError("Blix leaflet response is not an object")
        if "productOffers" not in payload:
            raise PromotionSourceContractError("Blix leaflet response has no productOffers")
        product_offers = payload["productOffers"]
        if not isinstance(product_offers, list):
            raise PromotionSourceContractError("Blix productOffers is not a list")

        offers: list[PromotionOffer] = []
        for item in product_offers:
            if not isinstance(item, dict):
                raise PromotionSourceContractError("Blix product offer entry is not an object")
            name = self._required_str(item, "name")
            brand_name = self._optional_str(item, "brandName")
            if not matches_query(name, brand_name, query):
                continue
            offer = self._map_offer(item, hit)
            offers.append(offer)
        return offers

    def _map_offer(self, offer: Mapping[str, object], hit: BlixLeafletHit) -> PromotionOffer:
        leaflet_id = self._required_int(offer, "leafletId")
        page_number = self._required_int(offer, "pageNumber")
        price_grosze = self._optional_int(offer, "price")

        shop_url = urljoin(self._base_url + "/", f"sklep/{hit.shop_slug}/")
        leaflet_url = urljoin(
            self._base_url + "/",
            f"sklep/{hit.shop_slug}/gazetka/{leaflet_id}/?pageNumber={page_number}",
        )

        provider_offer_id = self._optional_str(offer, "hash")
        name = self._required_str(offer, "name")
        image_url = self._required_str(offer, "image")
        brand_name = self._optional_str(offer, "brandName")
        price = None if price_grosze is None else Decimal(price_grosze) / Decimal(100)
        valid_from = self._required_date(offer, "dateStart")
        valid_until = self._required_date(offer, "dateEnd")
        return PromotionOffer(
            provider_offer_id=provider_offer_id,
            name=name,
            shop_name=hit.shop_name,
            shop_slug=hit.shop_slug,
            shop_url=shop_url,
            image_url=image_url,
            product_brand_name=brand_name,
            price=price,
            leaflet_provider_id=str(leaflet_id),
            leaflet_url=leaflet_url,
            page_number=page_number,
            valid_from=valid_from,
            valid_until=valid_until,
        )

    @staticmethod
    def _required_str(mapping: Mapping[str, object], key: str) -> str:
        value = mapping[key]
        if not isinstance(value, str) or not value.strip():
            raise PromotionSourceContractError(f"Blix field {key} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _optional_str(mapping: Mapping[str, object], key: str) -> str | None:
        value = mapping[key]
        if value is None:
            return None
        if not isinstance(value, str):
            raise PromotionSourceContractError(f"Blix field {key} must be a string or null")
        return value.strip() or None

    @staticmethod
    def _optional_int(mapping: Mapping[str, object], key: str) -> int | None:
        value = mapping[key]
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise PromotionSourceContractError(f"Blix field {key} must be an integer or null")
        return value

    @staticmethod
    def _required_int(mapping: Mapping[str, object], key: str) -> int:
        value = mapping[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise PromotionSourceContractError(f"Blix field {key} must be an integer")
        return value

    @classmethod
    def _required_date(cls, mapping: Mapping[str, object], key: str) -> date:
        value = mapping[key]
        if not isinstance(value, dict):
            raise PromotionSourceContractError(f"Blix field {key} must be an object")
        date_text = cls._required_str(value, "date")
        try:
            local = datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=_WARSAW)
            return local.date()
        except ValueError as error:
            raise PromotionSourceContractError(
                f"Blix field {key}.date has unsupported format: {date_text}"
            ) from error
