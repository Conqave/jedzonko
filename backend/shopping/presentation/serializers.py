from decimal import Decimal

from rest_framework import serializers


class HouseholdQuerySerializer(serializers.Serializer[dict[str, int]]):
    household_id = serializers.IntegerField(min_value=1)


class CreateShoppingListSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class RenameShoppingListSerializer(serializers.Serializer[dict[str, object]]):
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class AddShoppingListItemSerializer(serializers.Serializer[dict[str, object]]):
    product_id = serializers.IntegerField(
        min_value=1, required=False, allow_null=True, default=None
    )
    ingredient_id = serializers.IntegerField(
        min_value=1, required=False, allow_null=True, default=None
    )
    free_text = serializers.CharField(
        max_length=120, trim_whitespace=True, required=False, allow_null=True, default=None
    )
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    unit_code = serializers.CharField(max_length=16, required=False, allow_null=True, default=None)


class AddRecipeItemsSerializer(serializers.Serializer[dict[str, int]]):
    recipe_id = serializers.IntegerField(min_value=1)
    servings = serializers.IntegerField(min_value=1)


class ShoppingListSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(read_only=True)
    household_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    is_primary = serializers.BooleanField(read_only=True)
    item_count = serializers.IntegerField(read_only=True)


class ShoppingItemSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(read_only=True)
    list_id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(source="subject.product_id", read_only=True)
    ingredient_id = serializers.IntegerField(source="subject.ingredient_id", read_only=True)
    free_text = serializers.CharField(source="subject.free_text", read_only=True)
    name = serializers.CharField(read_only=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)
    unit_code = serializers.CharField(source="unit.code", read_only=True, allow_null=True)
    status = serializers.CharField(read_only=True)
    purchased_at = serializers.DateTimeField(read_only=True, allow_null=True)


class SplitByPromotionsSerializer(serializers.Serializer[dict[str, list[str]]]):
    shops = serializers.ListField(
        child=serializers.SlugField(max_length=120), min_length=1, max_length=20
    )


class AddExternalRecipeItemsSerializer(serializers.Serializer[dict[str, str]]):
    reference = serializers.SlugField(max_length=200)


class ChooseItemProductSerializer(serializers.Serializer[dict[str, int]]):
    product_id = serializers.IntegerField(min_value=1)


class PurchaseSerializer(serializers.Serializer[dict[str, int | None]]):
    item_id = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(
        min_value=1, required=False, allow_null=True, default=None
    )


class BuyItemsSerializer(serializers.Serializer[dict[str, list[dict[str, int | None]]]]):
    items = serializers.ListField(child=PurchaseSerializer(), min_length=1, max_length=200)


class DeleteItemsSerializer(serializers.Serializer[dict[str, list[int]]]):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), min_length=1, max_length=200
    )

    def validate_item_ids(self, item_ids: list[int]) -> list[int]:
        unique_ids = set(item_ids)
        if len(unique_ids) != len(item_ids):
            raise serializers.ValidationError("Each item is listed once.")
        return item_ids


class TagItemSerializer(serializers.Serializer[dict[str, object]]):
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    unit_code = serializers.CharField(max_length=16)


class ShoppingItemInterpretationSerializer(serializers.Serializer[object]):
    ingredient_id = serializers.IntegerField(read_only=True, allow_null=True)
    ingredient_name = serializers.CharField(read_only=True, allow_null=True)
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, read_only=True, allow_null=True
    )
    unit_code = serializers.CharField(read_only=True, allow_null=True)
