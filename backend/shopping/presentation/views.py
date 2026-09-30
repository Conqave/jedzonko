from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import current_user_id
from config.composition import container
from shopping.domain.shopping_subject import ShoppingSubject
from shopping.presentation.serializers import (
    AddExternalRecipeItemsSerializer,
    AddRecipeItemsSerializer,
    AddShoppingListItemSerializer,
    BuyItemsSerializer,
    ChooseItemProductSerializer,
    CreateShoppingListSerializer,
    HouseholdQuerySerializer,
    RenameShoppingListSerializer,
    ShoppingItemInterpretationSerializer,
    ShoppingItemSerializer,
    ShoppingListSerializer,
    SplitByPromotionsSerializer,
    TagItemSerializer,
)


class ShoppingListListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        query = HouseholdQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        use_case = container().shopping.list_shopping_lists
        lists = use_case.execute(user_id, query.validated_data["household_id"])
        serializer = ShoppingListSerializer(lists, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = CreateShoppingListSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().shopping.create_shopping_list
        shopping_list = use_case.execute(
            user_id, payload.validated_data["household_id"], payload.validated_data["name"]
        )
        serializer = ShoppingListSerializer(shopping_list)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ShoppingListDetailView(APIView):
    def patch(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        payload = RenameShoppingListSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().shopping.rename_shopping_list
        shopping_list = use_case.execute(user_id, list_id, payload.validated_data["name"])
        serializer = ShoppingListSerializer(shopping_list)
        return Response(serializer.data)

    def delete(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().shopping.delete_shopping_list
        use_case.execute(user_id, list_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListItemListView(APIView):
    def get(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().shopping.get_shopping_list_items
        items = use_case.execute(user_id, list_id)
        serializer = ShoppingItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        payload = AddShoppingListItemSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        subject = ShoppingSubject(
            product_id=data["product_id"],
            ingredient_id=data["ingredient_id"],
            free_text=data["free_text"],
        )
        use_case = container().shopping.add_shopping_list_item
        item = use_case.execute(user_id, list_id, subject, data["quantity"], data["unit_code"])
        serializer = ShoppingItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ShoppingListRecipeItemsView(APIView):
    def post(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        payload = AddRecipeItemsSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().shopping.add_missing_recipe_items_to_shopping_list
        items = use_case.execute(
            user_id,
            list_id,
            payload.validated_data["recipe_id"],
            payload.validated_data["servings"],
        )
        serializer = ShoppingItemSerializer(items, many=True)
        return Response(serializer.data)


class MinimumStockSynchronizationView(APIView):
    def post(self, request: Request, household_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().shopping.synchronize_minimum_stock
        items = use_case.execute(user_id, household_id)
        serializer = ShoppingItemSerializer(items, many=True)
        return Response(serializer.data)


class ShoppingItemPurchaseView(APIView):
    def post(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        now = timezone.now()
        use_case = container().shopping.buy_shopping_item
        use_case.execute(user_id, item_id, now)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingItemRestoreView(APIView):
    def post(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().shopping.restore_shopping_item
        item = use_case.execute(user_id, item_id)
        serializer = ShoppingItemSerializer(item)
        return Response(serializer.data)


class ShoppingItemDetailView(APIView):
    def delete(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().shopping.delete_shopping_list_item
        use_case.execute(user_id, item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListPurchaseView(APIView):
    def post(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        payload = BuyItemsSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        now = timezone.now()
        item_ids = tuple(payload.validated_data["item_ids"])
        container().shopping.buy_shopping_items.execute(user_id, list_id, item_ids, now)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListTaggingView(APIView):
    def post(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        now = timezone.now()
        items = container().shopping.tag_shopping_list.execute(user_id, list_id, now)
        serializer = ShoppingItemSerializer(items, many=True)
        return Response(serializer.data)


class ShoppingItemProductView(APIView):
    def put(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        payload = ChooseItemProductSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().shopping.choose_shopping_item_product
        item = use_case.execute(user_id, item_id, payload.validated_data["product_id"])
        serializer = ShoppingItemSerializer(item)
        return Response(serializer.data)


class ShoppingItemIngredientView(APIView):
    def put(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        payload = TagItemSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        use_case = container().shopping.tag_shopping_item
        item = use_case.execute(
            user_id, item_id, data["ingredient_id"], data["quantity"], data["unit_code"]
        )
        serializer = ShoppingItemSerializer(item)
        return Response(serializer.data)


class ShoppingItemInterpretationView(APIView):
    def post(self, request: Request, item_id: int) -> Response:
        user_id = current_user_id(request)
        now = timezone.now()
        use_case = container().shopping.interpret_shopping_item
        interpretation = use_case.execute(user_id, item_id, now)
        serializer = ShoppingItemInterpretationSerializer(interpretation)
        return Response(serializer.data)


class ShoppingListPromotionSplitView(APIView):
    def post(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        payload = SplitByPromotionsSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        shop_slugs = tuple(payload.validated_data["shops"])
        use_case = container().shopping.split_shopping_list_by_promotions
        lists = use_case.execute(user_id, list_id, shop_slugs)
        serializer = ShoppingListSerializer(lists, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ShoppingListExternalRecipeItemsView(APIView):
    def post(self, request: Request, list_id: int) -> Response:
        user_id = current_user_id(request)
        payload = AddExternalRecipeItemsSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().shopping.add_missing_external_recipe_items_to_shopping_list
        items = use_case.execute(user_id, list_id, payload.validated_data["reference"])
        serializer = ShoppingItemSerializer(items, many=True)
        return Response(serializer.data)
