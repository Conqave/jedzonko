from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from households.application.errors import NotAHouseholdMemberError
from households.models import IngredientTag
from shared.text import normalize_text
from recipes.application.ports.recipe_source import (
    RecipeNotFoundAtSourceError,
    RecipeSourceContractError,
    RecipeSourceUnavailable,
)
from recipes.application.use_cases.search_external_recipes import ExternalRecipeQuery
from recipes.composition import (
    build_get_external_recipe,
    build_search_external_recipes,
    build_suggest_external_recipes_from_inventory,
    open_recipe_source,
)
from recipes.presentation.errors import (
    RecipeSourceContractInvalidError,
    RecipeSourceUnavailableError,
)
from recipes.presentation.external_serializers import (
    ExternalRecipeSearchSerializer,
    ExternalRecipeSuggestionSerializer,
)
from recipes.presentation.representation import (
    represent_external_page,
    represent_external_recipe,
    represent_external_suggestions,
)


def _read_user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return user_id


def _split_names(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _remember_ania_tags(page: object) -> None:
    summaries = tuple(match.summary for match in page.matches)
    for summary in summaries:
        for name in summary.tag_names:
            IngredientTag.objects.get_or_create(
                normalized_name=normalize_text(name),
                defaults={"name": name, "source": "ania_gotuje"},
            )


class ExternalRecipeListView(APIView):
    def get(self, request: Request) -> Response:
        serializer = ExternalRecipeSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        query = ExternalRecipeQuery(
            household_id=int(payload["household_id"]),
            text=str(payload["query"]),
            ingredient_names=_split_names(str(payload["ingredients"])),
            excluded_ingredient_names=_split_names(str(payload["excluded_ingredients"])),
            page=int(payload["page"]),
            page_size=int(payload["page_size"]),
        )
        with open_recipe_source() as source:
            try:
                page = build_search_external_recipes(source).execute(_read_user_id(request), query)
                _remember_ania_tags(page)
            except NotAHouseholdMemberError:
                raise PermissionDenied(
                    detail="Not a household member.", code="not_a_household_member"
                )
            except RecipeSourceUnavailable:
                raise RecipeSourceUnavailableError
            except RecipeSourceContractError:
                raise RecipeSourceContractInvalidError
        return Response(represent_external_page(page))


class ExternalRecipeSuggestionListView(APIView):
    def get(self, request: Request) -> Response:
        serializer = ExternalRecipeSuggestionSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        with open_recipe_source() as source:
            try:
                suggestions = build_suggest_external_recipes_from_inventory(source).execute(
                    _read_user_id(request),
                    int(payload["household_id"]),
                    int(payload["page"]),
                    int(payload["page_size"]),
                )
                _remember_ania_tags(suggestions.page)
            except NotAHouseholdMemberError:
                raise PermissionDenied(
                    detail="Not a household member.", code="not_a_household_member"
                )
            except RecipeSourceUnavailable:
                raise RecipeSourceUnavailableError
            except RecipeSourceContractError:
                raise RecipeSourceContractInvalidError
        return Response(represent_external_suggestions(suggestions))


class ExternalRecipeDetailView(APIView):
    def get(self, request: Request, reference: str) -> Response:
        with open_recipe_source() as source:
            try:
                recipe = build_get_external_recipe(source).execute(reference)
            except RecipeNotFoundAtSourceError:
                raise NotFound(
                    detail="External recipe not found.", code="external_recipe_not_found"
                )
            except RecipeSourceUnavailable:
                raise RecipeSourceUnavailableError
            except RecipeSourceContractError:
                raise RecipeSourceContractInvalidError
        return Response(represent_external_recipe(recipe))
