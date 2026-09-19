from rest_framework.exceptions import APIException, NotAuthenticated, ValidationError
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
from promotions.application.use_cases.list_favourite_shops import ListFavouriteShops
from promotions.application.use_cases.list_promotion_shops import ListPromotionShops
from promotions.application.use_cases.search_promotions import SearchPromotions
from promotions.application.use_cases.set_favourite_shops import SetFavouriteShops, UnknownShopError
from promotions.composition import (
    build_favourite_shop_repository,
    build_search_result_limit,
    build_shop_selection,
    open_promotion_source,
)
from promotions.domain.models import FavouriteShop, PromotionOffer, Shop, StorePromotionCoverage
from promotions.presentation.permissions import CanViewPromotions
from promotions.presentation.serializers import (
    FavouriteShopsRequestSerializer,
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


def _represent_shop(shop: Shop) -> dict[str, object]:
    return {"name": shop.name, "slug": shop.slug, "url": shop.url}


def _represent_favourite_shop(favourite_shop: FavouriteShop) -> dict[str, object]:
    return {"name": favourite_shop.name, "slug": favourite_shop.slug}


def _represent_offer(offer: PromotionOffer) -> dict[str, object]:
    return {
        "provider_offer_id": offer.provider_offer_id,
        "name": offer.name,
        "shop_name": offer.shop_name,
        "shop_slug": offer.shop_slug,
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
        "shop_slug": coverage.shop_slug,
        "shop_url": coverage.shop_url,
        "matched_query_count": coverage.matched_query_count,
        "matched_queries": list(coverage.matched_queries),
        "offers": [_represent_offer(offer) for offer in coverage.offers],
    }


def _authenticated_user_id(request: Request) -> int:
    user_id = request.user.pk
    if not isinstance(user_id, int):
        raise NotAuthenticated
    return user_id


def _read_requested_shop_slugs(
    validated_data: dict[str, object], field_name: str
) -> tuple[str, ...] | None:
    if field_name not in validated_data:
        return None
    requested = validated_data[field_name]
    if not isinstance(requested, list):
        raise ValidationError(detail="shop selection must be a list", code="invalid")
    return tuple(str(shop_slug) for shop_slug in requested)


class PromotionShopsView(APIView):
    permission_classes = [CanViewPromotions]

    def get(self, request: Request) -> Response:
        with open_promotion_source() as source:
            use_case = ListPromotionShops(source)
            try:
                shops = use_case.execute()
            except PromotionSourceContractError as error:
                raise PromotionSourceContractInvalidError from error
            except PromotionSourceUnavailable as error:
                raise PromotionSourceUnavailableError from error
        return Response([_represent_shop(shop) for shop in shops])


class FavouriteShopsView(APIView):
    permission_classes = [CanViewPromotions]

    def get(self, request: Request) -> Response:
        use_case = ListFavouriteShops(build_favourite_shop_repository())
        favourite_shops = use_case.execute(_authenticated_user_id(request))
        return Response([_represent_favourite_shop(shop) for shop in favourite_shops])

    def put(self, request: Request) -> Response:
        serializer = FavouriteShopsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shop_slugs = tuple(str(shop_slug) for shop_slug in serializer.validated_data["shops"])
        with open_promotion_source() as source:
            use_case = SetFavouriteShops(build_favourite_shop_repository(), source)
            try:
                favourite_shops = use_case.execute(_authenticated_user_id(request), shop_slugs)
            except UnknownShopError as error:
                raise ValidationError(detail=str(error), code="unknown_shop") from error
            except PromotionSourceContractError as error:
                raise PromotionSourceContractInvalidError from error
            except PromotionSourceUnavailable as error:
                raise PromotionSourceUnavailableError from error
        return Response([_represent_favourite_shop(shop) for shop in favourite_shops])


class PromotionSearchView(APIView):
    permission_classes = [CanViewPromotions]

    def get(self, request: Request) -> Response:
        serializer = PromotionSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = str(serializer.validated_data["query"])
        requested_shop_slugs = _read_requested_shop_slugs(serializer.validated_data, "shop")
        with open_promotion_source() as source:
            use_case = SearchPromotions(source, build_shop_selection(), build_search_result_limit())
            try:
                offers = use_case.execute(
                    _authenticated_user_id(request), query, requested_shop_slugs
                )
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
        queries = [str(query) for query in serializer.validated_data["queries"]]
        requested_shop_slugs = _read_requested_shop_slugs(serializer.validated_data, "shops")
        with open_promotion_source() as source:
            use_case = CompareStorePromotionCoverage(source, build_shop_selection())
            try:
                coverage = use_case.execute(
                    _authenticated_user_id(request), queries, requested_shop_slugs
                )
            except ValueError as error:
                raise ValidationError(detail=str(error), code="invalid_query") from error
            except PromotionSourceContractError as error:
                raise PromotionSourceContractInvalidError from error
            except PromotionSourceUnavailable as error:
                raise PromotionSourceUnavailableError from error
        return Response([_represent_coverage(item) for item in coverage])
