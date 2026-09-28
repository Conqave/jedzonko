from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shopping.composition import (
    build_add_missing_recipe_items_to_shopping_list,
    build_add_shopping_list_item,
    build_buy_shopping_item,
    build_create_shopping_list,
    build_delete_shopping_list_item,
    build_get_shopping_list_items,
    build_list_shopping_lists,
    build_synchronize_minimum_stock,
)
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_list_summary import ShoppingListSummary
from shopping.models import PurchasedShoppingItem, ShoppingListItem, ShoppingList, PrimaryShoppingList
from households.models import HouseholdMembership
from shopping.presentation.error_mapping import HANDLED_ERRORS, to_api_exception
from shopping.presentation.serializers import (
    AddRecipeItemsSerializer,
    AddShoppingListItemSerializer,
    CreateShoppingListSerializer,
    RenameShoppingListSerializer,
    HouseholdQuerySerializer,
)


def _user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return user_id


def _represent_list(shopping_list: ShoppingListSummary) -> dict[str, object]:
    return {
        "id": shopping_list.id,
        "name": shopping_list.name,
        "is_primary": shopping_list.is_primary,
        "item_count": shopping_list.item_count,
    }


def _represent_item(item: ShoppingItemSnapshot) -> dict[str, object]:
    # Pending and purchased rows live in separate tables with independent id
    # spaces, so only the addressable pending rows expose an id over HTTP.
    return {
        "id": item.id,
        "product_id": item.product_id,
        "product_name": item.product_name,
        "free_text": item.free_text,
        "quantity": str(item.quantity),
        "unit_code": None if item.unit is None else item.unit.code,
        "is_purchased": item.is_purchased,
        "tag_names": list(item.tag_names),
    }


class ShoppingListListView(APIView):
    def get(self, request: Request) -> Response:
        query = HouseholdQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        household_id = int(query.validated_data["household_id"])
        try:
            shopping_lists = build_list_shopping_lists().execute(_user_id(request), household_id)
        except HANDLED_ERRORS as error:
            raise to_api_exception(error) from error
        return Response([_represent_list(item) for item in shopping_lists])

    def post(self, request: Request) -> Response:
        serializer = CreateShoppingListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        household_id = int(str(serializer.validated_data["household_id"]))
        name = str(serializer.validated_data["name"])
        try:
            shopping_list = build_create_shopping_list().execute(
                _user_id(request), household_id, name
            )
        except HANDLED_ERRORS as error:
            raise to_api_exception(error) from error
        return Response(_represent_list(shopping_list), status=status.HTTP_201_CREATED)

class ShoppingListDeleteView(APIView):
    def patch(self, request: Request, list_id: int) -> Response:
        serializer = RenameShoppingListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = ShoppingList.objects.filter(pk=list_id).first()
        if row is None or not HouseholdMembership.objects.filter(
            household_id=row.household_id, user_id=_user_id(request)
        ).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        row.name = str(serializer.validated_data["name"])
        row.save(update_fields=["name"])
        return Response(_represent_list(ShoppingListSummary(
            id=row.pk,
            name=row.name,
            is_primary=PrimaryShoppingList.objects.filter(shopping_list_id=row.pk).exists(),
            item_count=row.items.count() + row.purchased_items.count(),
        )))

    def delete(self, request: Request, list_id: int) -> Response:
        row = ShoppingList.objects.filter(pk=list_id).first()
        if row is None or not HouseholdMembership.objects.filter(household_id=row.household_id, user_id=_user_id(request)).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        row.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListItemListView(APIView):
    def get(self, request: Request, list_id: int) -> Response:
        try:
            items = build_get_shopping_list_items().execute(_user_id(request), list_id)
        except HANDLED_ERRORS as error:
            raise to_api_exception(error) from error
        return Response([_represent_item(item) for item in items])

    def post(self, request: Request, list_id: int) -> Response:
        serializer = AddShoppingListItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_product_id = serializer.validated_data.get("product_id")
        raw_free_text = serializer.validated_data.get("free_text")
        raw_unit_code = serializer.validated_data.get("unit_code")
        product_id = None if raw_product_id is None else int(str(raw_product_id))
        free_text = None if raw_free_text is None else str(raw_free_text)
        unit_code = None if raw_unit_code is None else str(raw_unit_code)
        quantity = Decimal(str(serializer.validated_data["quantity"]))
        try:
            item = build_add_shopping_list_item().execute(
                _user_id(request), list_id, product_id, free_text, quantity, unit_code
            )
        except HANDLED_ERRORS as error:
            raise to_api_exception(error) from error
        return Response(_represent_item(item), status=status.HTTP_201_CREATED)


class RecipeShoppingItemListView(APIView):
    def post(self, request: Request, list_id: int) -> Response:
        serializer = AddRecipeItemsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe_id = int(str(serializer.validated_data["recipe_id"]))
        servings = int(str(serializer.validated_data["servings"]))
        try:
            items = build_add_missing_recipe_items_to_shopping_list().execute(
                _user_id(request), list_id, recipe_id, servings
            )
        except HANDLED_ERRORS as error:
            raise to_api_exception(error) from error
        return Response([_represent_item(item) for item in items])


class MinimumStockSynchronizationView(APIView):
    def post(self, request: Request, list_id: int) -> Response:
        try:
            items = build_synchronize_minimum_stock().execute(_user_id(request), list_id)
        except HANDLED_ERRORS as error:
            raise to_api_exception(error) from error
        return Response([_represent_item(item) for item in items])


class ShoppingItemPurchaseView(APIView):
    def post(self, request: Request, item_id: int) -> Response:
        try:
            build_buy_shopping_item().execute(_user_id(request), item_id)
        except HANDLED_ERRORS as error:
            raise to_api_exception(error) from error
        return Response(status=status.HTTP_204_NO_CONTENT)


class PurchasedShoppingItemRestoreView(APIView):
    def post(self, request: Request, item_id: int) -> Response:
        row = PurchasedShoppingItem.objects.filter(pk=item_id).select_related("shopping_list").first()
        if row is None or not HouseholdMembership.objects.filter(
            household_id=row.shopping_list.household_id, user_id=_user_id(request)
        ).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        ShoppingListItem.objects.create(
            shopping_list_id=row.shopping_list_id,
            product_id=row.product_id,
            free_text=row.free_text,
            unit_code=row.unit_code,
            quantity=row.quantity,
            created_at=row.created_at,
        )
        row.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingItemDetailView(APIView):
    def delete(self, request: Request, item_id: int) -> Response:
        try:
            build_delete_shopping_list_item().execute(_user_id(request), item_id)
        except HANDLED_ERRORS as error:
            raise to_api_exception(error) from error
        return Response(status=status.HTTP_204_NO_CONTENT)
