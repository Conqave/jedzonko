from django.conf import settings
from rest_framework import serializers


class ExternalRecipeSearchSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    query = serializers.CharField(required=False, allow_blank=True, default="", max_length=120)
    ingredients = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=400
    )
    excluded_ingredients = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=400
    )
    page = serializers.IntegerField(min_value=0, required=False, default=0)
    page_size = serializers.IntegerField(
        min_value=1,
        max_value=settings.RECIPE_SOURCE_PAGE_SIZE_LIMIT,
        required=False,
        default=settings.RECIPE_SOURCE_PAGE_SIZE_LIMIT,
    )


class ExternalRecipeShortfallQuerySerializer(serializers.Serializer[dict[str, int]]):
    household_id = serializers.IntegerField(min_value=1)


class ExternalRecipeSuggestionSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    page = serializers.IntegerField(min_value=0, required=False, default=0)
    page_size = serializers.IntegerField(
        min_value=1,
        max_value=settings.RECIPE_SOURCE_PAGE_SIZE_LIMIT,
        required=False,
        default=settings.RECIPE_SOURCE_PAGE_SIZE_LIMIT,
    )


class ExternalRecipeMatchSerializer(serializers.Serializer[object]):
    source_name = serializers.CharField(source="summary.source_name", read_only=True)
    source_url = serializers.CharField(source="summary.source_url", read_only=True)
    reference = serializers.CharField(source="summary.reference", read_only=True)
    name = serializers.CharField(source="summary.name", read_only=True)
    description = serializers.CharField(source="summary.description", read_only=True)
    image_url = serializers.CharField(source="summary.image_url", read_only=True, allow_null=True)
    yield_label = serializers.CharField(source="summary.yield_label", read_only=True)
    total_time_minutes = serializers.IntegerField(
        source="summary.total_time_minutes", read_only=True, allow_null=True
    )
    tags = serializers.ListField(
        source="summary.tag_names", child=serializers.CharField(), read_only=True
    )
    matched_product_names = serializers.ListField(child=serializers.CharField(), read_only=True)


class MatchedExternalRecipePageSerializer(serializers.Serializer[object]):
    recipes = ExternalRecipeMatchSerializer(source="matches", many=True, read_only=True)
    page = serializers.IntegerField(read_only=True)
    page_size = serializers.IntegerField(read_only=True)
    total_count = serializers.IntegerField(read_only=True)
    total_pages = serializers.IntegerField(read_only=True)


class ExternalRecipeSuggestionsSerializer(serializers.Serializer[object]):
    page = MatchedExternalRecipePageSerializer(read_only=True)
    ingredient_names = serializers.ListField(child=serializers.CharField(), read_only=True)
    inventory_item_count = serializers.IntegerField(read_only=True)


class ExternalRecipeIngredientSerializer(serializers.Serializer[object]):
    source_text = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, read_only=True, allow_null=True
    )
    unit_code = serializers.CharField(read_only=True, allow_null=True)


class ExternalRecipeDetailSerializer(serializers.Serializer[object]):
    source_name = serializers.CharField(source="summary.source_name", read_only=True)
    source_url = serializers.CharField(source="summary.source_url", read_only=True)
    reference = serializers.CharField(source="summary.reference", read_only=True)
    name = serializers.CharField(source="summary.name", read_only=True)
    description = serializers.CharField(source="summary.description", read_only=True)
    image_url = serializers.CharField(source="summary.image_url", read_only=True, allow_null=True)
    yield_label = serializers.CharField(source="summary.yield_label", read_only=True)
    total_time_minutes = serializers.IntegerField(
        source="summary.total_time_minutes", read_only=True, allow_null=True
    )
    tags = serializers.ListField(
        source="summary.tag_names", child=serializers.CharField(), read_only=True
    )
    preparation_time_minutes = serializers.IntegerField(read_only=True)
    cooking_time_minutes = serializers.IntegerField(read_only=True)
    steps = serializers.ListField(child=serializers.CharField(), read_only=True)
    ingredients = ExternalRecipeIngredientSerializer(many=True, read_only=True)
