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


class ShopSerializer(serializers.Serializer[object]):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)


class FavouriteShopSerializer(serializers.Serializer[object]):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)


class PromotionOfferSerializer(serializers.Serializer[object]):
    provider_offer_id = serializers.CharField(read_only=True, allow_null=True)
    name = serializers.CharField(read_only=True)
    shop_name = serializers.CharField(read_only=True)
    shop_slug = serializers.CharField(read_only=True)
    shop_url = serializers.CharField(read_only=True)
    image_url = serializers.CharField(read_only=True)
    product_brand_name = serializers.CharField(read_only=True, allow_null=True)
    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True
    )
    leaflet_provider_id = serializers.CharField(read_only=True)
    leaflet_url = serializers.CharField(read_only=True)
    page_number = serializers.IntegerField(read_only=True)
    valid_from = serializers.DateField(read_only=True)
    valid_until = serializers.DateField(read_only=True)


class StorePromotionCoverageSerializer(serializers.Serializer[object]):
    shop_name = serializers.CharField(read_only=True)
    shop_slug = serializers.CharField(read_only=True)
    shop_url = serializers.CharField(read_only=True)
    matched_query_count = serializers.IntegerField(read_only=True)
    matched_queries = serializers.ListField(child=serializers.CharField(), read_only=True)
    offers = PromotionOfferSerializer(many=True, read_only=True)
