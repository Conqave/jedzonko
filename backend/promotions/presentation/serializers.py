from rest_framework import serializers


class PromotionSearchSerializer(serializers.Serializer[dict[str, str]]):
    query = serializers.CharField(max_length=120, trim_whitespace=True)


class StoreCoverageRequestSerializer(serializers.Serializer[dict[str, list[str]]]):
    queries = serializers.ListField(
        child=serializers.CharField(max_length=120, trim_whitespace=True),
        min_length=1,
        max_length=10,
    )
