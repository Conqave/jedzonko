from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from households.application.errors import NotAHouseholdMemberError
from inventory.application.errors import (
    DuplicateInventoryItemError,
    IngredientNotFoundError,
    InventoryItemNotFoundError,
    MeasurementUnitNotFoundError,
)
from inventory.composition import (
    build_add_inventory_item,
    build_delete_inventory_item,
    build_get_household_inventory,
    build_update_inventory_quantity,
)
from inventory.domain.models import InventoryItemSnapshot
from inventory.presentation.serializers import (
    AddInventoryItemSerializer,
    HouseholdQuerySerializer,
    UpdateInventoryQuantitySerializer,
)


def _current_user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return user_id


def _represent(item: InventoryItemSnapshot) -> dict[str, object]:
    return {
        "id": item.id,
        "ingredient_id": item.ingredient_id,
        "ingredient_name": item.ingredient_name,
        "quantity": str(item.quantity),
        "unit_code": item.unit.code,
        "minimum_quantity": None if item.minimum_quantity is None else str(item.minimum_quantity),
        "category_name": item.category_name,
        "photo_url": item.photo_url,
        "below_minimum": item.is_below_minimum(),
    }


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
                payload["ingredient_id"],
                payload["quantity"],
                payload["unit_code"],
                payload.get("minimum_quantity"),
                payload.get("category_id"),
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except DuplicateInventoryItemError:
            raise ValidationError(
                detail="This ingredient is already in the inventory.",
                code="duplicate_inventory_item",
            )
        except IngredientNotFoundError:
            raise ValidationError(detail="Unknown ingredient.", code="ingredient_not_found")
        except MeasurementUnitNotFoundError:
            raise ValidationError(
                detail="Unknown measurement unit.", code="measurement_unit_not_found"
            )
        return Response(_represent(item), status=status.HTTP_201_CREATED)


class InventoryItemView(APIView):
    def patch(self, request: Request, item_id: int) -> Response:
        serializer = UpdateInventoryQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = build_update_inventory_quantity().execute(
                _current_user_id(request), item_id, serializer.validated_data["quantity"]
            )
        except InventoryItemNotFoundError:
            raise NotFound(detail="Inventory item not found.", code="inventory_item_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response(_represent(item))

    def delete(self, request: Request, item_id: int) -> Response:
        try:
            build_delete_inventory_item().execute(_current_user_id(request), item_id)
        except InventoryItemNotFoundError:
            raise NotFound(detail="Inventory item not found.", code="inventory_item_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response(status=status.HTTP_204_NO_CONTENT)
