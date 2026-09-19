from recipes.domain.suggestion import RecipeSuggestion


def rank_suggestions(suggestions: list[RecipeSuggestion]) -> list[RecipeSuggestion]:
    return sorted(
        suggestions,
        key=lambda item: (
            not item.shortfall.is_ready,
            len(item.shortfall.missing_items),
            -item.shortfall.available_item_count,
            item.recipe_name,
        ),
    )
