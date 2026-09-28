from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import current_user_id
from config.composition import container
from inventory.presentation.photo_upload import InventoryPhotoUpload
from inventory.presentation.serializers import (
    AddInventoryItemSerializer,
    CreateInventoryCategorySerializer,
    HouseholdQuerySerializer,
    InventoryCategorySerializer,
    InventoryItemSerializer,
    SetInventoryItemCategorySerializer,
    UpdateInventoryItemSerializer,
)


class InventoryListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        query = HouseholdQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        use_case = container().inventory.get_household_inventory
        items = use_case.execute(user_id, query.validated_data["household_id"])
        serializer = InventoryItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = AddInventoryItemSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        use_case = container().inventory.add_inventory_item
        item = use_case.execute(
            user_id,
            data["household_id"],
            data["product_id"],
            data["quantity"],
            data["unit_code"],
            data.get("minimum_quantity"),
            data.get("category_id"),
        )
        serializer = InventoryItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InventoryItemView(APIView):
    def patch(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        payload = UpdateInventoryItemSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        use_case = container().inventory.update_inventory_item
        item = use_case.execute(
            user_id,
            item_id,
            data.get("product_name"),
            data.get("quantity"),
            data.get("unit_code"),
        )
        serializer = InventoryItemSerializer(item)
        return Response(serializer.data)

    def delete(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().inventory.delete_inventory_item
        use_case.execute(user_id, item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InventoryCategoryListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        query = HouseholdQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        use_case = container().inventory.list_inventory_categories
        categories = use_case.execute(user_id, query.validated_data["household_id"])
        serializer = InventoryCategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = CreateInventoryCategorySerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().inventory.create_inventory_category
        category = use_case.execute(
            user_id, payload.validated_data["household_id"], payload.validated_data["name"]
        )
        serializer = InventoryCategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InventoryItemCategoryView(APIView):
    def put(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        payload = SetInventoryItemCategorySerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().inventory.set_inventory_item_category
        item = use_case.execute(user_id, item_id, payload.validated_data["category_id"])
        serializer = InventoryItemSerializer(item)
        return Response(serializer.data)


class InventoryItemPhotoView(APIView):
    parser_classes = [MultiPartParser]

    def put(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        uploaded = request.FILES.get("photo")
        if uploaded is None:
            raise ValidationError(detail="No photo was sent.", code="photo_required")
        photo = InventoryPhotoUpload.read(uploaded)
        use_case = container().inventory.set_inventory_item_photo
        item = use_case.execute(user_id, item_id, photo)
        serializer = InventoryItemSerializer(item)
        return Response(serializer.data)

    def delete(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().inventory.delete_inventory_item_photo
        item = use_case.execute(user_id, item_id)
        serializer = InventoryItemSerializer(item)
        return Response(serializer.data)
