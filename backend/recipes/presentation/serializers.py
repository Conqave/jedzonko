from rest_framework import serializers

from recipes.domain.difficulty import RecipeDifficulty


class RecipeStepSerializer(serializers.Serializer[dict[str, object]]):
    position = serializers.IntegerField(min_value=1)
    text = serializers.CharField(trim_whitespace=True)


class RecipeIngredientSerializer(serializers.Serializer[dict[str, object]]):
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0)
    unit_code = serializers.CharField(max_length=16, trim_whitespace=True)


class RecipeWriteSerializer(serializers.Serializer[dict[str, object]]):
    name = serializers.CharField(max_length=160, trim_whitespace=True)
    description = serializers.CharField(allow_blank=True, trim_whitespace=True)
    servings = serializers.IntegerField(min_value=1)
    preparation_time_minutes = serializers.IntegerField(min_value=0)
    cooking_time_minutes = serializers.IntegerField(min_value=0)
    difficulty = serializers.ChoiceField(choices=[item.value for item in RecipeDifficulty])
    category_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=60, trim_whitespace=True), required=False
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
