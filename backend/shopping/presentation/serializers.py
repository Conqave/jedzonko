from decimal import Decimal

from rest_framework import serializers


class HouseholdQuerySerializer(serializers.Serializer[dict[str, int]]):
    household_id = serializers.IntegerField(min_value=1)


class CreateShoppingListSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class AddShoppingListItemSerializer(serializers.Serializer[dict[str, object]]):
    ingredient_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    free_text = serializers.CharField(
        max_length=120, trim_whitespace=True, required=False, allow_null=True
    )
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0"))
    unit_code = serializers.CharField(max_length=16, required=False, allow_null=True)


class AddRecipeItemsSerializer(serializers.Serializer[dict[str, int]]):
    recipe_id = serializers.IntegerField(min_value=1)
    servings = serializers.IntegerField(min_value=1)
