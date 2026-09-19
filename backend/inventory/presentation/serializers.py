from rest_framework import serializers


class AddInventoryItemSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0)
    unit_code = serializers.CharField(max_length=16, trim_whitespace=True)
    minimum_quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=0, required=False, allow_null=True
    )
    category_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)


class UpdateInventoryItemSerializer(serializers.Serializer[dict[str, object]]):
    product_name = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=0, required=False
    )
    unit_code = serializers.CharField(max_length=16, trim_whitespace=True, required=False)

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        if not attrs:
            raise serializers.ValidationError(
                detail="Nothing to update.", code="empty_inventory_update"
            )
        return attrs


class HouseholdQuerySerializer(serializers.Serializer[dict[str, int]]):
    household_id = serializers.IntegerField(min_value=1)


class CreateInventoryCategorySerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=80, trim_whitespace=True)


class SetInventoryItemCategorySerializer(serializers.Serializer[dict[str, object]]):
    category_id = serializers.IntegerField(min_value=1, allow_null=True)
