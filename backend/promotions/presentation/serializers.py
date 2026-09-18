from rest_framework import serializers


class PromotionSearchSerializer(serializers.Serializer[dict[str, object]]):
    query = serializers.CharField(max_length=120, trim_whitespace=True)
    shop = serializers.ListField(
        child=serializers.SlugField(max_length=120),
        required=False,
        max_length=20,
    )


class StoreCoverageRequestSerializer(serializers.Serializer[dict[str, object]]):
    queries = serializers.ListField(
        child=serializers.CharField(max_length=120, trim_whitespace=True),
        min_length=1,
        max_length=10,
    )
    shops = serializers.ListField(
        child=serializers.SlugField(max_length=120),
        required=False,
        max_length=20,
    )


class FavouriteShopsRequestSerializer(serializers.Serializer[dict[str, object]]):
    shops = serializers.ListField(
        child=serializers.SlugField(max_length=120),
        max_length=20,
    )
