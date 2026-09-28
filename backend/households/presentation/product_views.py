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
from households.models import HouseholdMembership, IngredientTag, Product, ProductTag
from households.tag_analysis_jobs import get as get_tag_job, start as start_tag_job
from shared.text import normalize_text
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


class ProductTagListView(APIView):
    def get(self, request: Request, product_id: int) -> Response:
        product = Product.objects.filter(
            pk=product_id, household__memberships__user_id=_current_user_id(request)
        ).first()
        if product is None:
            raise PermissionDenied(detail="Product not found.", code="product_not_found")
        return Response([
            {"id": tag.id, "name": tag.ingredient_tag.name, "source": tag.source, "is_verified": tag.is_verified}
            for tag in product.product_tags.select_related("ingredient_tag").all()
        ])

    def post(self, request: Request, product_id: int) -> Response:
        product = Product.objects.filter(
            pk=product_id, household__memberships__user_id=_current_user_id(request)
        ).first()
        if product is None:
            raise PermissionDenied(detail="Product not found.", code="product_not_found")
        name = str(request.data.get("name", "")).strip()
        if not name:
            raise ValidationError(detail="Tag name is required.", code="tag_name_required")
        ingredient_tag = IngredientTag.objects.filter(
            normalized_name=normalize_text(name), source="ania_gotuje"
        ).first()
        if ingredient_tag is None:
            raise ValidationError(
                detail="Tag musi pochodzić z katalogu Ania Gotuje.", code="tag_not_in_ania_catalog"
            )
        tag, _ = ProductTag.objects.get_or_create(
            product=product, ingredient_tag=ingredient_tag,
            defaults={"source": "manual", "is_verified": True},
        )
        return Response(
            {"id": tag.id, "name": ingredient_tag.name, "source": tag.source, "is_verified": tag.is_verified},
            status=status.HTTP_201_CREATED,
        )


class ProductTagDetailView(APIView):
    def delete(self, request: Request, tag_id: int) -> Response:
        tag = ProductTag.objects.filter(
            pk=tag_id, product__household__memberships__user_id=_current_user_id(request)
        ).first()
        if tag is None:
            raise PermissionDenied(detail="Tag not found.", code="tag_not_found")
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductTagOptionsView(APIView):
    def get(self, request: Request) -> Response:
        search = normalize_text(str(request.query_params.get("search", "")))
        tags = IngredientTag.objects.filter(
            source="ania_gotuje",
            product_tags__product__household__memberships__user_id=_current_user_id(request)
        )
        household_id = request.query_params.get("household_id")
        if household_id is not None:
            tags = tags.filter(product_tags__product__household_id=household_id)
        if search:
            tags = tags.filter(normalized_name__contains=search)
        names = list(tags.order_by("name").values_list("name", flat=True).distinct()[:20])
        return Response(names)

class TagAnalysisStartView(APIView):
    def post(self, request: Request, household_id: int) -> Response:
        if not HouseholdMembership.objects.filter(household_id=household_id, user_id=_current_user_id(request)).exists():
            raise PermissionDenied
        product_id = request.data.get("product_id")
        item_id = request.data.get("item_id")
        text = request.data.get("text")
        if product_id is not None and not Product.objects.filter(
            id=product_id, household_id=household_id
        ).exists():
            raise PermissionDenied
        if product_id is None and (item_id is None or not str(text or "").strip()):
            return Response({"detail": "Wymagany jest produkt albo tekst pozycji."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"job_id": start_tag_job(
                household_id,
                int(product_id) if product_id is not None else None,
                int(item_id) if item_id is not None else None,
                str(text).strip() if text else None,
            )},
            status=status.HTTP_202_ACCEPTED,
        )

class TagAnalysisStatusView(APIView):
    def get(self, request: Request, job_id: str) -> Response:
        job = get_tag_job(job_id)
        if job is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(job)
