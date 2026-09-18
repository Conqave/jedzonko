from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from promotions.application.ports.promotion_source import (
    PromotionSourceContractError,
    PromotionSourceUnavailable,
)
from promotions.application.use_cases.compare_store_promotion_coverage import (
    CompareStorePromotionCoverage,
)
from promotions.application.use_cases.search_promotions import SearchPromotions
from promotions.composition import open_promotion_source
from promotions.domain.models import PromotionOffer, StorePromotionCoverage
from promotions.presentation.permissions import CanViewPromotions
from promotions.presentation.serializers import (
    PromotionSearchSerializer,
    StoreCoverageRequestSerializer,
)


class PromotionSourceUnavailableError(APIException):
    status_code = 503
    default_detail = "The promotion provider is currently unavailable."
    default_code = "promotion_source_unavailable"


class PromotionSourceContractInvalidError(APIException):
    status_code = 502
    default_detail = "The promotion provider returned an unexpected response."
    default_code = "promotion_source_contract_invalid"


def _represent_offer(offer: PromotionOffer) -> dict[str, object]:
    return {
        "provider_offer_id": offer.provider_offer_id,
        "name": offer.name,
        "shop_name": offer.shop_name,
        "shop_url": offer.shop_url,
        "image_url": offer.image_url,
        "product_brand_name": offer.product_brand_name,
        "price": None if offer.price is None else str(offer.price),
        "leaflet_provider_id": offer.leaflet_provider_id,
        "leaflet_url": offer.leaflet_url,
        "page_number": offer.page_number,
        "valid_from": offer.valid_from.isoformat(),
        "valid_until": offer.valid_until.isoformat(),
    }


def _represent_coverage(coverage: StorePromotionCoverage) -> dict[str, object]:
    return {
        "shop_name": coverage.shop_name,
        "shop_url": coverage.shop_url,
        "matched_query_count": coverage.matched_query_count,
        "matched_queries": list(coverage.matched_queries),
        "offers": [_represent_offer(offer) for offer in coverage.offers],
    }


class PromotionSearchView(APIView):
    permission_classes = [CanViewPromotions]

    def get(self, request: Request) -> Response:
        serializer = PromotionSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        with open_promotion_source() as source:
            use_case = SearchPromotions(source)
            try:
                offers = use_case.execute(serializer.validated_data["query"])
            except PromotionSourceContractError as error:
                raise PromotionSourceContractInvalidError from error
            except PromotionSourceUnavailable as error:
                raise PromotionSourceUnavailableError from error
        return Response([_represent_offer(offer) for offer in offers])


class StorePromotionCoverageView(APIView):
    permission_classes = [CanViewPromotions]

    def post(self, request: Request) -> Response:
        serializer = StoreCoverageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with open_promotion_source() as source:
            use_case = CompareStorePromotionCoverage(source)
            try:
                coverage = use_case.execute(serializer.validated_data["queries"])
            except ValueError as error:
                raise ValidationError(detail=str(error), code="invalid_query") from error
            except PromotionSourceContractError as error:
                raise PromotionSourceContractInvalidError from error
            except PromotionSourceUnavailable as error:
                raise PromotionSourceUnavailableError from error
        return Response([_represent_coverage(item) for item in coverage])
