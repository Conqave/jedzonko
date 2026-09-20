from recipes.application.use_cases.suggest_external_recipes_from_inventory import (
    ExternalRecipeSuggestions,
)
from recipes.domain.external import (
    ExternalRecipeDetail,
    ExternalRecipeMatch,
    ExternalRecipeSummary,
    MatchedExternalRecipePage,
)
from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.domain.suggestion import MissingRecipeItem, RecipeShortfall, RecipeSuggestion


def represent_summary(summary: RecipeSummary) -> dict[str, object]:
    return {
        "id": summary.id,
        "name": summary.name,
        "description": summary.description,
        "servings": summary.servings,
        "preparation_time_minutes": summary.preparation_time_minutes,
        "cooking_time_minutes": summary.cooking_time_minutes,
        "difficulty": summary.difficulty.value,
        "category_name": summary.category_name,
        "tags": list(summary.tag_names),
        "image_url": summary.image_url,
        "author_username": summary.author_username,
    }


def represent_detail(detail: RecipeDetail) -> dict[str, object]:
    payload = represent_summary(detail.summary)
    payload["steps"] = [{"position": step.position, "text": step.text} for step in detail.steps]
    payload["ingredients"] = [
        {"name": item.name, "quantity": str(item.quantity), "unit_code": item.unit_code}
        for item in detail.ingredients
    ]
    return payload


def represent_missing_item(item: MissingRecipeItem) -> dict[str, object]:
    return {"name": item.name, "amount": str(item.amount), "unit_code": item.unit_code}


def represent_shortfall(shortfall: RecipeShortfall) -> dict[str, object]:
    return {
        "missing_items": [represent_missing_item(item) for item in shortfall.missing_items],
        "required_item_count": shortfall.required_item_count,
        "available_item_count": shortfall.available_item_count,
        "unmeasured_ingredients": list(shortfall.unmeasured_ingredient_names),
        "is_ready": shortfall.is_ready,
    }


def represent_suggestion(suggestion: RecipeSuggestion) -> dict[str, object]:
    payload = represent_shortfall(suggestion.shortfall)
    payload["recipe_id"] = suggestion.recipe_id
    payload["recipe_name"] = suggestion.recipe_name
    payload["missing_item_count"] = len(suggestion.shortfall.missing_items)
    return payload


def represent_external_summary(summary: ExternalRecipeSummary) -> dict[str, object]:
    return {
        "source_name": summary.source_name,
        "source_url": summary.source_url,
        "reference": summary.reference,
        "name": summary.name,
        "description": summary.description,
        "image_url": summary.image_url,
        "yield_label": summary.yield_label,
        "total_time_minutes": summary.total_time_minutes,
        "tags": list(summary.tag_names),
    }


def represent_external_match(match: ExternalRecipeMatch) -> dict[str, object]:
    payload = represent_external_summary(match.summary)
    payload["matched_product_names"] = list(match.matched_product_names)
    payload["matched_product_count"] = len(match.matched_product_names)
    return payload


def represent_external_page(page: MatchedExternalRecipePage) -> dict[str, object]:
    return {
        "recipes": [represent_external_match(match) for match in page.matches],
        "page": page.page,
        "page_size": page.page_size,
        "total_count": page.total_count,
        "total_pages": page.total_pages,
    }


def represent_external_suggestions(suggestions: ExternalRecipeSuggestions) -> dict[str, object]:
    payload = represent_external_page(suggestions.page)
    payload["ingredient_names"] = list(suggestions.ingredient_names)
    payload["inventory_item_count"] = suggestions.inventory_item_count
    return payload


def represent_external_recipe(detail: ExternalRecipeDetail) -> dict[str, object]:
    summary = detail.summary
    return {
        "source_name": summary.source_name,
        "source_url": summary.source_url,
        "reference": summary.reference,
        "name": summary.name,
        "description": summary.description,
        "image_url": summary.image_url,
        "yield_label": summary.yield_label,
        "total_time_minutes": summary.total_time_minutes,
        "preparation_time_minutes": detail.preparation_time_minutes,
        "cooking_time_minutes": detail.cooking_time_minutes,
        "tags": list(summary.tag_names),
        "steps": list(detail.steps),
        "ingredients": [
            {
                "source_text": item.source_text,
                "name": item.name,
                "quantity": None if item.quantity is None else str(item.quantity),
                "unit_code": item.unit_code,
            }
            for item in detail.ingredients
        ],
    }
