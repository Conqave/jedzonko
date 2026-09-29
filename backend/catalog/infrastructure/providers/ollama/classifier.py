import re

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.application.ports.ingredient_classifier import IngredientClassifier
from catalog.infrastructure.providers.ollama.prompt import build_classification_prompt
from shared.infrastructure.ollama_chat import (
    OllamaChat,
    OllamaContractError,
    OllamaUnavailableError,
)

_INTEGER_PATTERN = re.compile(r"\d+")


class OllamaIngredientClassifier(IngredientClassifier):
    def __init__(self, chat: OllamaChat) -> None:
        self._chat = chat

    @property
    def model_name(self) -> str:
        return self._chat.model_name

    def find_matching_ingredient(
        self, product_name: str, ingredient_names: tuple[str, ...]
    ) -> int | None:
        if not ingredient_names:
            raise ValueError("ingredient_names must not be empty")
        prompt = build_classification_prompt(product_name, ingredient_names)
        content = self._ask(prompt)
        return self._read_choice(content, len(ingredient_names))

    def _ask(self, prompt: str) -> str:
        try:
            return self._chat.ask(prompt)
        except OllamaUnavailableError as error:
            raise IngredientClassifierUnavailableError(str(error)) from error
        except OllamaContractError as error:
            raise IngredientClassifierContractError(str(error)) from error

    @staticmethod
    def _read_choice(content: str, ingredient_count: int) -> int | None:
        numbers = _INTEGER_PATTERN.findall(content)
        if not numbers:
            raise IngredientClassifierContractError(
                f"Ollama answered without a number: {content[:200]!r}"
            )
        choice = int(numbers[-1])
        if choice == 0:
            return None
        if choice > ingredient_count:
            raise IngredientClassifierContractError(
                f"Ollama answered {choice} for a list of {ingredient_count} ingredients."
            )
        return choice - 1
