from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import current_user_id
from config.composition import container
from recipes.application.commands import RecipeIngredientInput, RecipeInput, RecipeStepInput
from recipes.domain.difficulty import RecipeDifficulty
from recipes.presentation.serializers import (
    ConfirmPreparationSerializer,
    MissingItemsQuerySerializer,
    RecipeCategorySerializer,
    RecipeDetailSerializer,
    RecipeNutritionSerializer,
    RecipeShortfallSerializer,
    RecipeSuggestionSerializer,
    RecipeSummarySerializer,
    RecipeWriteSerializer,
    SuggestionQuerySerializer,
)


def _read_recipe_input(request: Request) -> RecipeInput:
    payload = RecipeWriteSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    data = payload.validated_data
    steps = tuple(
        RecipeStepInput(position=step["position"], text=step["text"]) for step in data["steps"]
    )
    ingredients = tuple(
        RecipeIngredientInput(
            name=line["name"], quantity=line["quantity"], unit_code=line["unit_code"]
        )
        for line in data["ingredients"]
    )
    difficulty = RecipeDifficulty(data["difficulty"])
    return RecipeInput(
        name=data["name"],
        description=data["description"],
        servings=data["servings"],
        preparation_time_minutes=data["preparation_time_minutes"],
        cooking_time_minutes=data["cooking_time_minutes"],
        difficulty=difficulty,
        category_id=data["category_id"],
        tag_names=tuple(data["tag_names"]),
        steps=steps,
        ingredients=ingredients,
    )


class RecipeListView(APIView):
    def get(self, request: Request) -> Response:
        use_case = container().recipes.list_recipes
        recipes = use_case.execute()
        serializer = RecipeSummarySerializer(recipes, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        user_id = current_user_id(request)
        command = _read_recipe_input(request)
        use_case = container().recipes.create_recipe
        recipe = use_case.execute(user_id, command)
        serializer = RecipeDetailSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeCategoryListView(APIView):
    def get(self, request: Request) -> Response:
        use_case = container().recipes.list_recipe_categories
        categories = use_case.execute()
        serializer = RecipeCategorySerializer(categories, many=True)
        return Response(serializer.data)


class RecipeDetailView(APIView):
    def get(self, request: Request, recipe_id: int) -> Response:
        use_case = container().recipes.get_recipe
        recipe = use_case.execute(recipe_id)
        serializer = RecipeDetailSerializer(recipe)
        return Response(serializer.data)

    def put(self, request: Request, recipe_id: int) -> Response:
        command = _read_recipe_input(request)
        use_case = container().recipes.update_recipe
        recipe = use_case.execute(recipe_id, command)
        serializer = RecipeDetailSerializer(recipe)
        return Response(serializer.data)

    def delete(self, request: Request, recipe_id: int) -> Response:
        use_case = container().recipes.delete_recipe
        use_case.execute(recipe_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeNutritionView(APIView):
    def get(self, request: Request, recipe_id: int) -> Response:
        use_case = container().recipes.get_recipe_nutrition
        nutrition = use_case.execute(recipe_id)
        serializer = RecipeNutritionSerializer(nutrition)
        return Response(serializer.data)


class RecipeSuggestionListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        query = SuggestionQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        use_case = container().recipes.suggest_recipes_from_inventory
        suggestions = use_case.execute(user_id, query.validated_data["household_id"])
        serializer = RecipeSuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)


class RecipeMissingItemListView(APIView):
    def get(self, request: Request, recipe_id: int) -> Response:
        user_id = current_user_id(request)
        query = MissingItemsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        use_case = container().recipes.calculate_missing_recipe_items
        shortfall = use_case.execute(
            user_id,
            query.validated_data["household_id"],
            recipe_id,
            query.validated_data["servings"],
        )
        serializer = RecipeShortfallSerializer(shortfall)
        return Response(serializer.data)


class RecipePreparationView(APIView):
    def post(self, request: Request, recipe_id: int) -> Response:
        user_id = current_user_id(request)
        payload = ConfirmPreparationSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().recipes.confirm_recipe_preparation
        use_case.execute(
            user_id,
            payload.validated_data["household_id"],
            recipe_id,
            payload.validated_data["servings"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
