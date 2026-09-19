from django.conf import settings
from rest_framework import serializers


class ExternalRecipeSearchSerializer(serializers.Serializer[dict[str, object]]):
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


class ExternalRecipeSuggestionSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    page = serializers.IntegerField(min_value=0, required=False, default=0)
    page_size = serializers.IntegerField(
        min_value=1,
        max_value=settings.RECIPE_SOURCE_PAGE_SIZE_LIMIT,
        required=False,
        default=settings.RECIPE_SOURCE_PAGE_SIZE_LIMIT,
    )
