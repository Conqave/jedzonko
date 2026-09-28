from households.application.ports.ingredient_matcher import (
    IngredientMatcher,
    IngredientMatcherUnavailable,
)


class FakeIngredientMatcher(IngredientMatcher):
    def __init__(self, answers: dict[str, str]) -> None:
        self._answers = answers
        self.questions: list[tuple[str, tuple[str, ...]]] = []

    @property
    def model_name(self) -> str:
        return "fake-model"

    def find_matching_product(
        self, ingredient_name: str, product_names: tuple[str, ...]
    ) -> int | None:
        self.questions.append((ingredient_name, product_names))
        expected = self._answers.get(ingredient_name)
        if expected is None or expected not in product_names:
            return None
        return product_names.index(expected)


class UnavailableIngredientMatcher(IngredientMatcher):
    def __init__(self) -> None:
        self.questions: list[str] = []

    @property
    def model_name(self) -> str:
        return "dead-model"

    def find_matching_product(
        self, ingredient_name: str, product_names: tuple[str, ...]
    ) -> int | None:
        self.questions.append(ingredient_name)
        raise IngredientMatcherUnavailable("Ollama request failed: http://127.0.0.1:1/api/chat")
