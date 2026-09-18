from recipes.domain.suggestion import RecipeSuggestion


def rank_suggestions(suggestions: list[RecipeSuggestion]) -> list[RecipeSuggestion]:
    return sorted(
        suggestions,
        key=lambda item: (item.missing_item_count, -item.available_item_count, item.recipe_name),
    )
