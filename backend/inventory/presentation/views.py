from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from households.application.errors import (
    DuplicateProductError,
    NotAHouseholdMemberError,
)
from inventory.application.errors import (
    DuplicateInventoryCategoryError,
    DuplicateInventoryItemError,
    InventoryCategoryNotFoundError,
    InventoryItemNotFoundError,
    InventoryPhotoNotFoundError,
    MeasurementUnitNotFoundError,
    ProductNotFoundError,
)
from inventory.composition import (
    build_add_inventory_item,
    build_create_inventory_category,
    build_delete_inventory_item,
    build_delete_inventory_item_photo,
    build_get_household_inventory,
    build_list_inventory_categories,
    build_set_inventory_item_category,
    build_set_inventory_item_photo,
    build_update_inventory_item,
)
from inventory.domain.category import InventoryCategorySnapshot
from inventory.domain.models import InventoryItemSnapshot
from inventory.presentation.photo_upload import InventoryPhotoUpload
from inventory.presentation.serializers import (
    AddInventoryItemSerializer,
    CreateInventoryCategorySerializer,
    HouseholdQuerySerializer,
    SetInventoryItemCategorySerializer,
    UpdateInventoryItemSerializer,
)


def _current_user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return user_id


def _represent(item: InventoryItemSnapshot) -> dict[str, object]:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "product_name": item.product_name,
        "tags": list(item.tag_names),
        "quantity": str(item.quantity),
        "unit_code": item.unit.code,
        "minimum_quantity": None if item.minimum_quantity is None else str(item.minimum_quantity),
        "category_id": item.category_id,
        "category_name": item.category_name,
        "photo_url": item.photo_url,
        "below_minimum": item.is_below_minimum(),
    }


def _represent_category(category: InventoryCategorySnapshot) -> dict[str, object]:
    return {"id": category.id, "name": category.name}


class InventoryListView(APIView):
    def get(self, request: Request) -> Response:
        query = HouseholdQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        try:
            items = build_get_household_inventory().execute(
                _current_user_id(request), query.validated_data["household_id"]
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response([_represent(item) for item in items])

    def post(self, request: Request) -> Response:
        serializer = AddInventoryItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        try:
            item = build_add_inventory_item().execute(
                _current_user_id(request),
                payload["household_id"],
                payload["product_id"],
                payload["quantity"],
                payload["unit_code"],
                payload.get("minimum_quantity"),
                payload.get("category_id"),
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except DuplicateInventoryItemError:
            raise ValidationError(
                detail="This product is already in the inventory.",
                code="duplicate_inventory_item",
            )
        except InventoryCategoryNotFoundError:
            raise ValidationError(
                detail="Unknown inventory category.", code="inventory_category_not_found"
            )
        except ProductNotFoundError:
            raise ValidationError(detail="Unknown product.", code="product_not_found")
        except MeasurementUnitNotFoundError:
            raise ValidationError(
                detail="Unknown measurement unit.", code="measurement_unit_not_found"
            )
        return Response(_represent(item), status=status.HTTP_201_CREATED)


class InventoryItemView(APIView):
    def patch(self, request: Request, item_id: int) -> Response:
        serializer = UpdateInventoryItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        try:
            item = build_update_inventory_item().execute(
                _current_user_id(request),
                item_id,
                payload.get("product_name"),
                payload.get("quantity"),
                payload.get("unit_code"),
            )
        except InventoryItemNotFoundError:
            raise NotFound(detail="Inventory item not found.", code="inventory_item_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except DuplicateProductError:
            raise ValidationError(
                detail="A product with this name already exists.", code="duplicate_product"
            )
        except MeasurementUnitNotFoundError:
            raise ValidationError(
                detail="Unknown measurement unit.", code="measurement_unit_not_found"
            )
        return Response(_represent(item))

    def delete(self, request: Request, item_id: int) -> Response:
        try:
            build_delete_inventory_item().execute(_current_user_id(request), item_id)
        except InventoryItemNotFoundError:
            raise NotFound(detail="Inventory item not found.", code="inventory_item_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response(status=status.HTTP_204_NO_CONTENT)


class InventoryCategoryListView(APIView):
    def get(self, request: Request) -> Response:
        query = HouseholdQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        try:
            categories = build_list_inventory_categories().execute(
                _current_user_id(request), query.validated_data["household_id"]
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response([_represent_category(category) for category in categories])

    def post(self, request: Request) -> Response:
        serializer = CreateInventoryCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        try:
            category = build_create_inventory_category().execute(
                _current_user_id(request), payload["household_id"], payload["name"]
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except DuplicateInventoryCategoryError:
            raise ValidationError(
                detail="This category already exists.", code="duplicate_inventory_category"
            )
        return Response(_represent_category(category), status=status.HTTP_201_CREATED)


class InventoryItemCategoryView(APIView):
    def put(self, request: Request, item_id: int) -> Response:
        serializer = SetInventoryItemCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = build_set_inventory_item_category().execute(
                _current_user_id(request), item_id, serializer.validated_data["category_id"]
            )
        except InventoryItemNotFoundError:
            raise NotFound(detail="Inventory item not found.", code="inventory_item_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except InventoryCategoryNotFoundError:
            raise ValidationError(
                detail="Unknown inventory category.", code="inventory_category_not_found"
            )
        return Response(_represent(item))


class InventoryItemPhotoView(APIView):
    parser_classes = [MultiPartParser]

    def put(self, request: Request, item_id: int) -> Response:
        uploaded = request.FILES.get("photo")
        if uploaded is None:
            raise ValidationError(detail="No photo was sent.", code="photo_required")
        photo = InventoryPhotoUpload.read(uploaded)
        try:
            item = build_set_inventory_item_photo().execute(
                _current_user_id(request), item_id, photo
            )
        except InventoryItemNotFoundError:
            raise NotFound(detail="Inventory item not found.", code="inventory_item_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response(_represent(item))

    def delete(self, request: Request, item_id: int) -> Response:
        try:
            item = build_delete_inventory_item_photo().execute(_current_user_id(request), item_id)
        except InventoryItemNotFoundError:
            raise NotFound(detail="Inventory item not found.", code="inventory_item_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except InventoryPhotoNotFoundError:
            raise NotFound(detail="This item has no photo.", code="inventory_photo_not_found")
        return Response(_represent(item))
