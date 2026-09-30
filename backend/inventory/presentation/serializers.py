from rest_framework import serializers

from shared.presentation.serializers import ItemCaloriesSerializer


class AddInventoryItemSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0)
    unit_code = serializers.CharField(max_length=16, trim_whitespace=True)
    minimum_quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=0, required=False, allow_null=True, default=None
    )


class UpdateInventoryItemSerializer(serializers.Serializer[dict[str, object]]):
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


class SetInventoryItemMinimumSerializer(serializers.Serializer[dict[str, object]]):
    minimum_quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=0, allow_null=True
    )


class InventoryItemSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(source="item.id", read_only=True)
    product_id = serializers.IntegerField(source="item.product_id", read_only=True)
    product_name = serializers.CharField(source="item.product_name", read_only=True)
    quantity = serializers.DecimalField(
        source="item.quantity", max_digits=12, decimal_places=3, read_only=True
    )
    unit_code = serializers.CharField(source="item.unit.code", read_only=True)
    minimum_quantity = serializers.DecimalField(
        source="item.minimum_quantity",
        max_digits=12,
        decimal_places=3,
        read_only=True,
        allow_null=True,
    )
    photo_url = serializers.CharField(source="item.photo_url", read_only=True, allow_null=True)
    below_minimum = serializers.BooleanField(source="item.is_below_minimum", read_only=True)
    calories = ItemCaloriesSerializer(read_only=True)
