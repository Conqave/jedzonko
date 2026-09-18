from rest_framework import serializers


class AddInventoryItemSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0)
    unit_code = serializers.CharField(max_length=16, trim_whitespace=True)
    minimum_quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=0, required=False, allow_null=True
    )
    category_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)


class UpdateInventoryQuantitySerializer(serializers.Serializer[dict[str, object]]):
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0)


class HouseholdQuerySerializer(serializers.Serializer[dict[str, int]]):
    household_id = serializers.IntegerField(min_value=1)
