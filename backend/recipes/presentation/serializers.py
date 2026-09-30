from decimal import Decimal

from rest_framework import serializers

from recipes.domain.difficulty import RecipeDifficulty


class RecipeStepSerializer(serializers.Serializer[dict[str, object]]):
    position = serializers.IntegerField(min_value=1)
    text = serializers.CharField(trim_whitespace=True)


class RecipeIngredientSerializer(serializers.Serializer[dict[str, object]]):
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    unit_code = serializers.CharField(max_length=16, trim_whitespace=True)


class RecipeWriteSerializer(serializers.Serializer[dict[str, object]]):
    name = serializers.CharField(max_length=160, trim_whitespace=True)
    description = serializers.CharField(allow_blank=True, trim_whitespace=True)
    servings = serializers.IntegerField(min_value=1)
    preparation_time_minutes = serializers.IntegerField(min_value=0)
    cooking_time_minutes = serializers.IntegerField(min_value=0)
    difficulty = serializers.ChoiceField(choices=[item.value for item in RecipeDifficulty])
    category_id = serializers.IntegerField(
        min_value=1, required=False, allow_null=True, default=None
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=60, trim_whitespace=True), default=list
    )
    steps = RecipeStepSerializer(many=True)
    ingredients = RecipeIngredientSerializer(many=True)


class SuggestionQuerySerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)


class MissingItemsQuerySerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    servings = serializers.IntegerField()


class ConfirmPreparationSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    servings = serializers.IntegerField()


class RecipeCategorySerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class RecipeStepDetailSerializer(serializers.Serializer[object]):
    position = serializers.IntegerField(read_only=True)
    text = serializers.CharField(read_only=True)


class RecipeIngredientDetailSerializer(serializers.Serializer[object]):
    name = serializers.CharField(read_only=True)
    ingredient_id = serializers.IntegerField(read_only=True, allow_null=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)
    unit_code = serializers.CharField(read_only=True)


class RecipeDetailSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(source="summary.id", read_only=True)
    name = serializers.CharField(source="summary.name", read_only=True)
    description = serializers.CharField(source="summary.description", read_only=True)
    servings = serializers.IntegerField(source="summary.servings", read_only=True)
    preparation_time_minutes = serializers.IntegerField(
        source="summary.preparation_time_minutes", read_only=True
    )
    cooking_time_minutes = serializers.IntegerField(
        source="summary.cooking_time_minutes", read_only=True
    )
    difficulty = serializers.CharField(source="summary.difficulty", read_only=True)
    category = RecipeCategorySerializer(source="summary.category", read_only=True, allow_null=True)
    tags = serializers.ListField(
        source="summary.tag_names", child=serializers.CharField(), read_only=True
    )
    image_url = serializers.CharField(source="summary.image_url", read_only=True, allow_null=True)
    author_username = serializers.CharField(
        source="summary.author_username", read_only=True, allow_null=True
    )
    steps = RecipeStepDetailSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientDetailSerializer(many=True, read_only=True)


class MissingRecipeItemSerializer(serializers.Serializer[object]):
    name = serializers.CharField(read_only=True)
    ingredient_id = serializers.IntegerField(read_only=True, allow_null=True)
    stocked_product_id = serializers.IntegerField(read_only=True, allow_null=True)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=3, read_only=True, allow_null=True
    )
    unit_code = serializers.CharField(read_only=True, allow_null=True)


class RecipeShortfallSerializer(serializers.Serializer[object]):
    missing_items = MissingRecipeItemSerializer(many=True, read_only=True)
    required_item_count = serializers.IntegerField(read_only=True)
    available_item_count = serializers.IntegerField(read_only=True)
    unmeasured_ingredients = serializers.ListField(
        source="unmeasured_ingredient_names", child=serializers.CharField(), read_only=True
    )
    is_ready = serializers.BooleanField(read_only=True)


class RecipeSuggestionSerializer(serializers.Serializer[object]):
    recipe_id = serializers.IntegerField(read_only=True)
    recipe_name = serializers.CharField(read_only=True)
    shortfall = RecipeShortfallSerializer(read_only=True)


class UncountedIngredientSerializer(serializers.Serializer[object]):
    name = serializers.CharField(read_only=True)
    reason = serializers.CharField(read_only=True)


class RecipeNutritionSerializer(serializers.Serializer[object]):
    total_kcal = serializers.DecimalField(max_digits=12, decimal_places=1, read_only=True)
    kcal_per_serving = serializers.DecimalField(
        max_digits=12, decimal_places=1, read_only=True, allow_null=True
    )
    has_estimates = serializers.BooleanField(read_only=True)
    uncounted_ingredients = UncountedIngredientSerializer(many=True, read_only=True)


class RecipeListingSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(source="summary.id", read_only=True)
    name = serializers.CharField(source="summary.name", read_only=True)
    description = serializers.CharField(source="summary.description", read_only=True)
    servings = serializers.IntegerField(source="summary.servings", read_only=True)
    preparation_time_minutes = serializers.IntegerField(
        source="summary.preparation_time_minutes", read_only=True
    )
    cooking_time_minutes = serializers.IntegerField(
        source="summary.cooking_time_minutes", read_only=True
    )
    difficulty = serializers.CharField(source="summary.difficulty", read_only=True)
    category = RecipeCategorySerializer(source="summary.category", read_only=True, allow_null=True)
    tags = serializers.ListField(
        source="summary.tag_names", child=serializers.CharField(), read_only=True
    )
    image_url = serializers.CharField(source="summary.image_url", read_only=True, allow_null=True)
    author_username = serializers.CharField(
        source="summary.author_username", read_only=True, allow_null=True
    )
    nutrition = RecipeNutritionSerializer(read_only=True)
    ingredient_names = serializers.ListField(child=serializers.CharField(), read_only=True)
