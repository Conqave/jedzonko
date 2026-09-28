from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import current_user_id
from config.composition import container
from promotions.presentation.permissions import CanViewPromotions
from promotions.presentation.serializers import (
    FavouriteShopSerializer,
    FavouriteShopsRequestSerializer,
    PromotionOfferSerializer,
    PromotionSearchSerializer,
    ShopSerializer,
    StoreCoverageRequestSerializer,
    StorePromotionCoverageSerializer,
)


class PromotionShopsView(APIView):
    permission_classes = [CanViewPromotions]

    def get(self, request: Request) -> Response:
        with container().promotions.open_source() as promotions:
            shops = promotions.list_shops.execute()
        serializer = ShopSerializer(shops, many=True)
        return Response(serializer.data)


class FavouriteShopsView(APIView):
    permission_classes = [CanViewPromotions]

    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        use_case = container().promotions.list_favourite_shops
        shops = use_case.execute(user_id)
        serializer = FavouriteShopSerializer(shops, many=True)
        return Response(serializer.data)

    def put(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = FavouriteShopsRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        shop_slugs = tuple(payload.validated_data["shops"])
        with container().promotions.open_source() as promotions:
            shops = promotions.set_favourite_shops.execute(user_id, shop_slugs)
        serializer = FavouriteShopSerializer(shops, many=True)
        return Response(serializer.data)


class PromotionSearchView(APIView):
    permission_classes = [CanViewPromotions]

    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        query = PromotionSearchSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        shops = query.validated_data.get("shop")
        shop_slugs = None if shops is None else tuple(shops)
        with container().promotions.open_source() as promotions:
            offers = promotions.search.execute(user_id, query.validated_data["query"], shop_slugs)
        serializer = PromotionOfferSerializer(offers, many=True)
        return Response(serializer.data)


class StorePromotionCoverageView(APIView):
    permission_classes = [CanViewPromotions]

    def post(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = StoreCoverageRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        queries = list(payload.validated_data["queries"])
        shops = payload.validated_data.get("shops")
        shop_slugs = None if shops is None else tuple(shops)
        with container().promotions.open_source() as promotions:
            coverage = promotions.compare_store_coverage.execute(user_id, queries, shop_slugs)
        serializer = StorePromotionCoverageSerializer(coverage, many=True)
        return Response(serializer.data)
