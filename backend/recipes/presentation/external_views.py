from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import current_user_id
from config.composition import container
from recipes.application.use_cases.search_external_recipes import ExternalRecipeQuery
from recipes.presentation.external_serializers import (
    ExternalRecipeDetailSerializer,
    ExternalRecipeSearchSerializer,
    ExternalRecipeShortfallQuerySerializer,
    ExternalRecipeSuggestionSerializer,
    ExternalRecipeSuggestionsSerializer,
    MatchedExternalRecipePageSerializer,
)
from recipes.presentation.serializers import RecipeShortfallSerializer


def _split_names(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


class ExternalRecipeListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = ExternalRecipeSearchSerializer(data=request.query_params)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        ingredient_names = _split_names(data["ingredients"])
        excluded_ingredient_names = _split_names(data["excluded_ingredients"])
        query = ExternalRecipeQuery(
            household_id=data["household_id"],
            text=data["query"],
            ingredient_names=ingredient_names,
            excluded_ingredient_names=excluded_ingredient_names,
            page=data["page"],
            page_size=data["page_size"],
        )
        with container().recipes.open_external() as external:
            page = external.search.execute(user_id, query)
        serializer = MatchedExternalRecipePageSerializer(page)
        return Response(serializer.data)


class ExternalRecipeSuggestionListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = ExternalRecipeSuggestionSerializer(data=request.query_params)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        with container().recipes.open_external() as external:
            suggestions = external.suggest_from_inventory.execute(
                user_id, data["household_id"], data["page"], data["page_size"]
            )
        serializer = ExternalRecipeSuggestionsSerializer(suggestions)
        return Response(serializer.data)


class ExternalRecipeDetailView(APIView):
    def get(self, request: Request, reference: str) -> Response:
        with container().recipes.open_external() as external:
            recipe = external.get.execute(reference)
        serializer = ExternalRecipeDetailSerializer(recipe)
        return Response(serializer.data)


class ExternalRecipeMissingItemListView(APIView):
    def get(self, request: Request, reference: str) -> Response:
        user_id = current_user_id(request)
        query = ExternalRecipeShortfallQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        household_id = query.validated_data["household_id"]
        with container().recipes.open_external() as external:
            shortfall = external.calculate_shortfall.execute(user_id, household_id, reference)
        serializer = RecipeShortfallSerializer(shortfall)
        return Response(serializer.data)
