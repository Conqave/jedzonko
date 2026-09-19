from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from households.application.errors import (
    DuplicateProductError,
    MeasurementUnitNotFoundError,
    NotAHouseholdMemberError,
)
from households.composition import build_create_household_product, build_list_household_products
from households.domain.product import ProductSummary
from households.presentation.serializers import CreateProductSerializer, ProductQuerySerializer


def _current_user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return user_id


def _represent_product(product: ProductSummary) -> dict[str, object]:
    return {
        "id": product.id,
        "household_id": product.household_id,
        "name": product.name,
        "default_unit_code": product.default_unit_code,
        "is_food": product.is_food,
    }


class ProductListView(APIView):
    def get(self, request: Request) -> Response:
        query = ProductQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        raw_search = query.validated_data.get("search")
        search = None if raw_search is None else str(raw_search)
        try:
            products = build_list_household_products().execute(
                _current_user_id(request), int(query.validated_data["household_id"]), search
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response([_represent_product(product) for product in products])

    def post(self, request: Request) -> Response:
        serializer = CreateProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        try:
            product = build_create_household_product().execute(
                _current_user_id(request),
                int(payload["household_id"]),
                str(payload["name"]),
                str(payload["default_unit_code"]),
                bool(payload["is_food"]),
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except MeasurementUnitNotFoundError:
            raise ValidationError(
                detail="Unknown measurement unit.", code="measurement_unit_not_found"
            )
        except DuplicateProductError:
            raise ValidationError(
                detail="This product already exists in the household.", code="duplicate_product"
            )
        return Response(_represent_product(product), status=status.HTTP_201_CREATED)
