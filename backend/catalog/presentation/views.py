from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.presentation.serializers import (
    CreateProductSerializer,
    IngredientQuerySerializer,
    IngredientSerializer,
    MeasurementUnitSerializer,
    ProductIngredientLinkSerializer,
    ProductListingSerializer,
    ProductQuerySerializer,
    ProductSerializer,
    SetTagCaloriesSerializer,
    UpdateProductSerializer,
    to_package,
)
from config.api import current_user_id
from config.composition import container


class ProductListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        query = ProductQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        use_case = container().catalog.list_household_products
        listings = use_case.execute(
            user_id, query.validated_data["household_id"], query.validated_data.get("search")
        )
        serializer = ProductListingSerializer(listings, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = CreateProductSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        package = to_package(data["package"])
        use_case = container().catalog.create_product
        product = use_case.execute(
            user_id,
            data["household_id"],
            data["name"],
            data["default_unit_code"],
            data["is_food"],
            package,
        )
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    def patch(self, request: Request, product_id: int) -> Response:
        user_id = current_user_id(request)
        payload = UpdateProductSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        package = to_package(payload.validated_data["package"])
        use_case = container().catalog.update_product
        product = use_case.execute(user_id, product_id, payload.validated_data["name"], package)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def delete(self, request: Request, product_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().catalog.delete_product
        use_case.execute(user_id, product_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductIngredientListView(APIView):
    def get(self, request: Request, product_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().catalog.get_product_classification
        links = use_case.execute(user_id, product_id)
        serializer = ProductIngredientLinkSerializer(links, many=True)
        return Response(serializer.data)


class ProductIngredientAnalysisView(APIView):
    def post(self, request: Request, product_id: int) -> Response:
        user_id = current_user_id(request)
        now = timezone.now()
        with container().catalog.open_product_analysis() as analysis:
            proposals = analysis.execute(user_id, product_id, now)
        return Response({"assigned_count": len(proposals)})


class ProductIngredientConfirmationView(APIView):
    def post(self, request: Request, product_id: int, ingredient_id: int) -> Response:
        user_id = current_user_id(request)
        now = timezone.now()
        use_case = container().catalog.confirm_product_ingredient
        use_case.execute(user_id, product_id, ingredient_id, now)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductIngredientRejectionView(APIView):
    def post(self, request: Request, product_id: int, ingredient_id: int) -> Response:
        user_id = current_user_id(request)
        now = timezone.now()
        use_case = container().catalog.reject_product_ingredient
        use_case.execute(user_id, product_id, ingredient_id, now)
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientListView(APIView):
    def get(self, request: Request) -> Response:
        query = IngredientQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        use_case = container().catalog.search_ingredients
        ingredients = use_case.execute(query.validated_data["search"])
        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data)


class IngredientCaloriesView(APIView):
    def put(self, request: Request, ingredient_id: int) -> Response:
        payload = SetTagCaloriesSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().catalog.set_tag_calories
        ingredient = use_case.execute(ingredient_id, payload.validated_data["kcal_per_100g"])
        serializer = IngredientSerializer(ingredient)
        return Response(serializer.data)


class MeasurementUnitListView(APIView):
    def get(self, request: Request) -> Response:
        use_case = container().catalog.list_measurement_units
        units = use_case.execute()
        serializer = MeasurementUnitSerializer(units, many=True)
        return Response(serializer.data)
