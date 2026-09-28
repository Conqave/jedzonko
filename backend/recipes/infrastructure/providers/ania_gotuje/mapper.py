from recipes.application.errors import RecipeSourceContractError
from recipes.domain.external import (
    ExternalRecipeDetail,
    ExternalRecipeIngredient,
    ExternalRecipePage,
    ExternalRecipeSummary,
)
from recipes.infrastructure.providers.ania_gotuje.duration import parse_iso_duration_minutes
from recipes.infrastructure.providers.ania_gotuje.html_text import read_paragraphs, read_plain_text
from recipes.infrastructure.providers.ania_gotuje.ingredient_line import parse_ingredient_line

SOURCE_NAME = "Ania Gotuje"
RECIPE_PAGE_BASE_URL = "https://aniagotuje.pl/przepis"
_TAG_CATEGORY_TYPE = "TAG"
_MAX_TAG_COUNT = 12


class AniaGotujeRecipeMapper:
    def map_detail(self, payload: object) -> ExternalRecipeDetail:
        if not isinstance(payload, dict):
            raise RecipeSourceContractError("Recipe payload is not a JSON object.")
        try:
            return self._build_detail(payload)
        except KeyError as error:
            raise RecipeSourceContractError(
                f"Recipe payload is missing field {error.args[0]!r}."
            ) from error

    def map_page(self, payload: object) -> ExternalRecipePage:
        if not isinstance(payload, dict):
            raise RecipeSourceContractError("Search payload is not a JSON object.")
        try:
            return self._build_page(payload)
        except KeyError as error:
            raise RecipeSourceContractError(
                f"Search payload is missing field {error.args[0]!r}."
            ) from error

    def _build_page(self, payload: dict[str, object]) -> ExternalRecipePage:
        content = payload["content"]
        if not isinstance(content, list):
            raise RecipeSourceContractError("Search payload 'content' is not a list.")
        recipes: list[ExternalRecipeSummary] = []
        for entry in content:
            if not isinstance(entry, dict):
                raise RecipeSourceContractError("Search result entry is not a JSON object.")
            total_time_minutes = self._read_optional_int(entry, "recipeTotalTimeMinutes")
            summary = self._build_summary(entry, total_time_minutes)
            recipes.append(summary)
        page = self._read_int(payload, "number")
        page_size = self._read_int(payload, "size")
        total_count = self._read_int(payload, "totalElements")
        total_pages = self._read_int(payload, "totalPages")
        return ExternalRecipePage(
            recipes=tuple(recipes),
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
        )

    def _build_detail(self, payload: dict[str, object]) -> ExternalRecipeDetail:
        total_time = self._read_text(payload, "recipeTotalTime")
        preparation_time = self._read_text(payload, "recipePrepTime")
        cooking_time = self._read_text(payload, "recipeCookTime")
        body = self._read_text(payload, "body")
        total_time_minutes = parse_iso_duration_minutes(total_time)
        summary = self._build_summary(payload, total_time_minutes)
        preparation_time_minutes = parse_iso_duration_minutes(preparation_time)
        cooking_time_minutes = parse_iso_duration_minutes(cooking_time)
        steps = read_paragraphs(body)
        ingredients = self._read_ingredients(payload)
        return ExternalRecipeDetail(
            summary=summary,
            preparation_time_minutes=preparation_time_minutes,
            cooking_time_minutes=cooking_time_minutes,
            steps=tuple(steps),
            ingredients=ingredients,
        )

    def _build_summary(
        self, payload: dict[str, object], total_time_minutes: int | None
    ) -> ExternalRecipeSummary:
        slug = self._read_text(payload, "slug")
        name = self._read_text(payload, "title")
        intro = self._read_optional_text(payload, "intro")
        description = read_plain_text(intro)
        image_url = self._read_thumbnail_url(payload)
        yield_label = self._read_optional_text(payload, "recipeYield")
        tag_names = self._read_tag_names(payload)
        return ExternalRecipeSummary(
            source_name=SOURCE_NAME,
            source_url=f"{RECIPE_PAGE_BASE_URL}/{slug}",
            reference=slug,
            name=name,
            description=description,
            image_url=image_url,
            yield_label=yield_label,
            total_time_minutes=total_time_minutes,
            tag_names=tag_names,
        )

    def _read_ingredients(self, payload: dict[str, object]) -> tuple[ExternalRecipeIngredient, ...]:
        groups = payload["ingredients"]
        if not isinstance(groups, list) or not groups:
            raise RecipeSourceContractError("Recipe payload has no ingredient groups.")
        ingredients: list[ExternalRecipeIngredient] = []
        for group in groups:
            if not isinstance(group, dict):
                raise RecipeSourceContractError("Ingredient group is not a JSON object.")
            items = group["items"]
            if not isinstance(items, list):
                raise RecipeSourceContractError("Ingredient group 'items' is not a list.")
            for item in items:
                if not isinstance(item, dict):
                    raise RecipeSourceContractError("Ingredient item is not a JSON object.")
                line = self._read_text(item, "name")
                ingredient = parse_ingredient_line(line)
                ingredients.append(ingredient)
        if not ingredients:
            raise RecipeSourceContractError("Recipe payload has no ingredients.")
        return tuple(ingredients)

    def _read_tag_names(self, payload: dict[str, object]) -> tuple[str, ...]:
        categories = payload["categories"]
        if not isinstance(categories, list):
            raise RecipeSourceContractError("Recipe payload 'categories' is not a list.")
        names: list[str] = []
        for category in categories:
            if not isinstance(category, dict):
                raise RecipeSourceContractError("Category entry is not a JSON object.")
            if self._read_text(category, "type") != _TAG_CATEGORY_TYPE:
                continue
            name = self._read_text(category, "name")
            if name not in names:
                names.append(name)
        return tuple(names[:_MAX_TAG_COUNT])

    def _read_thumbnail_url(self, payload: dict[str, object]) -> str | None:
        thumbnail = payload.get("postThumb")
        if thumbnail is None:
            return None
        if not isinstance(thumbnail, dict):
            raise RecipeSourceContractError("Recipe payload 'postThumb' is not a JSON object.")
        return self._read_text(thumbnail, "url")

    @staticmethod
    def _read_text(payload: dict[str, object], key: str) -> str:
        value = payload[key]
        if not isinstance(value, str) or not value.strip():
            raise RecipeSourceContractError(f"Recipe payload field {key!r} is not a text value.")
        return value.strip()

    @staticmethod
    def _read_optional_text(payload: dict[str, object], key: str) -> str:
        value = payload.get(key)
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _read_int(payload: dict[str, object], key: str) -> int:
        value = payload[key]
        if not isinstance(value, int) or isinstance(value, bool):
            raise RecipeSourceContractError(f"Payload field {key!r} is not an integer.")
        return value

    @staticmethod
    def _read_optional_int(payload: dict[str, object], key: str) -> int | None:
        value = payload.get(key)
        if value is None or isinstance(value, bool):
            return None
        if not isinstance(value, int):
            raise RecipeSourceContractError(f"Payload field {key!r} is not an integer.")
        return value
