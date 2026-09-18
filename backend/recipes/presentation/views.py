from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from households.application.errors import NotAHouseholdMemberError
from recipes.application.commands import RecipeIngredientInput, RecipeInput, RecipeStepInput
from recipes.application.errors import (
    IngredientNotFoundError,
    InvalidServingsError,
    MeasurementUnitNotFoundError,
    RecipeCategoryNotFoundError,
    RecipeNotFoundError,
)
from recipes.composition import (
    build_calculate_missing_recipe_items,
    build_confirm_recipe_preparation,
    build_create_recipe,
    build_delete_recipe,
    build_get_recipe,
    build_list_recipes,
    build_suggest_recipes_from_inventory,
    build_update_recipe,
)
from recipes.domain.difficulty import RecipeDifficulty
from recipes.presentation.representation import (
    represent_detail,
    represent_missing_item,
    represent_suggestion,
    represent_summary,
)
from recipes.presentation.serializers import (
    ConfirmPreparationSerializer,
    MissingItemsQuerySerializer,
    RecipeWriteSerializer,
    SuggestionQuerySerializer,
)


def _read_user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return user_id


def _read_recipe_input(request: Request) -> RecipeInput:
    serializer = RecipeWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    steps = tuple(
        RecipeStepInput(position=int(step["position"]), text=str(step["text"]))
        for step in payload["steps"]
    )
    ingredients = tuple(
        RecipeIngredientInput(
            ingredient_id=int(item["ingredient_id"]),
            quantity=Decimal(item["quantity"]),
            unit_code=str(item["unit_code"]),
        )
        for item in payload["ingredients"]
    )
    category_id = payload.get("category_id")
    return RecipeInput(
        name=str(payload["name"]),
        description=str(payload["description"]),
        servings=int(payload["servings"]),
        preparation_time_minutes=int(payload["preparation_time_minutes"]),
        cooking_time_minutes=int(payload["cooking_time_minutes"]),
        difficulty=RecipeDifficulty(payload["difficulty"]),
        category_id=None if category_id is None else int(category_id),
        tag_names=tuple(str(name) for name in payload.get("tag_names", [])),
        steps=steps,
        ingredients=ingredients,
    )


class RecipeListView(APIView):
    def get(self, request: Request) -> Response:
        recipes = build_list_recipes().execute()
        return Response([represent_summary(item) for item in recipes])

    def post(self, request: Request) -> Response:
        command = _read_recipe_input(request)
        try:
            recipe = build_create_recipe().execute(_read_user_id(request), command)
        except IngredientNotFoundError:
            raise ValidationError(detail="Ingredient not found.", code="ingredient_not_found")
        except MeasurementUnitNotFoundError:
            raise ValidationError(
                detail="Measurement unit not found.", code="measurement_unit_not_found"
            )
        except RecipeCategoryNotFoundError:
            raise ValidationError(
                detail="Recipe category not found.", code="recipe_category_not_found"
            )
        return Response(represent_detail(recipe), status=status.HTTP_201_CREATED)


class RecipeDetailView(APIView):
    def get(self, request: Request, recipe_id: int) -> Response:
        try:
            recipe = build_get_recipe().execute(recipe_id)
        except RecipeNotFoundError:
            raise NotFound(detail="Recipe not found.", code="recipe_not_found")
        return Response(represent_detail(recipe))

    def put(self, request: Request, recipe_id: int) -> Response:
        command = _read_recipe_input(request)
        try:
            recipe = build_update_recipe().execute(recipe_id, command)
        except RecipeNotFoundError:
            raise NotFound(detail="Recipe not found.", code="recipe_not_found")
        except IngredientNotFoundError:
            raise ValidationError(detail="Ingredient not found.", code="ingredient_not_found")
        except MeasurementUnitNotFoundError:
            raise ValidationError(
                detail="Measurement unit not found.", code="measurement_unit_not_found"
            )
        except RecipeCategoryNotFoundError:
            raise ValidationError(
                detail="Recipe category not found.", code="recipe_category_not_found"
            )
        return Response(represent_detail(recipe))

    def delete(self, request: Request, recipe_id: int) -> Response:
        try:
            build_delete_recipe().execute(recipe_id)
        except RecipeNotFoundError:
            raise NotFound(detail="Recipe not found.", code="recipe_not_found")
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeSuggestionListView(APIView):
    def get(self, request: Request) -> Response:
        serializer = SuggestionQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        household_id = int(serializer.validated_data["household_id"])
        try:
            suggestions = build_suggest_recipes_from_inventory().execute(
                _read_user_id(request), household_id
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response([represent_suggestion(item) for item in suggestions])


class RecipeMissingItemListView(APIView):
    def get(self, request: Request, recipe_id: int) -> Response:
        serializer = MissingItemsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        household_id = int(serializer.validated_data["household_id"])
        servings = int(serializer.validated_data["servings"])
        try:
            items = build_calculate_missing_recipe_items().execute(
                _read_user_id(request), household_id, recipe_id, servings
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except InvalidServingsError:
            raise ValidationError(detail="Servings must be at least 1.", code="invalid_servings")
        except RecipeNotFoundError:
            raise NotFound(detail="Recipe not found.", code="recipe_not_found")
        return Response([represent_missing_item(item) for item in items])


class RecipePreparationView(APIView):
    def post(self, request: Request, recipe_id: int) -> Response:
        serializer = ConfirmPreparationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        household_id = int(serializer.validated_data["household_id"])
        servings = int(serializer.validated_data["servings"])
        try:
            build_confirm_recipe_preparation().execute(
                _read_user_id(request), household_id, recipe_id, servings
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except InvalidServingsError:
            raise ValidationError(detail="Servings must be at least 1.", code="invalid_servings")
        except RecipeNotFoundError:
            raise NotFound(detail="Recipe not found.", code="recipe_not_found")
        except MeasurementUnitNotFoundError:
            raise ValidationError(
                detail="Measurement unit not found.", code="measurement_unit_not_found"
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
