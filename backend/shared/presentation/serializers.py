from rest_framework import serializers


class ItemCaloriesSerializer(serializers.Serializer[object]):
    kcal = serializers.DecimalField(
        max_digits=12, decimal_places=1, read_only=True, allow_null=True
    )
    kcal_per_100g = serializers.DecimalField(
        max_digits=12, decimal_places=1, read_only=True, allow_null=True
    )
    is_estimate = serializers.BooleanField(read_only=True)
    uncounted_reason = serializers.CharField(read_only=True, allow_null=True)
