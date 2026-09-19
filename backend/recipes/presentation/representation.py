from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.domain.suggestion import MissingRecipeItem, RecipeSuggestion


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


def represent_suggestion(suggestion: RecipeSuggestion) -> dict[str, object]:
    return {
        "recipe_id": suggestion.recipe_id,
        "recipe_name": suggestion.recipe_name,
        "available_item_count": suggestion.available_item_count,
        "missing_item_count": suggestion.missing_item_count,
        "missing_items": [represent_missing_item(item) for item in suggestion.missing_items],
    }
