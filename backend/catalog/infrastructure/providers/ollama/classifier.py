import json

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.application.ports.ingredient_classifier import IngredientClassifier
from catalog.infrastructure.providers.ollama.prompt import (
    build_classification_prompt,
    build_classification_schema,
)
from shared.infrastructure.ollama_chat import (
    OllamaChat,
    OllamaContractError,
    OllamaUnavailableError,
)


class OllamaIngredientClassifier(IngredientClassifier):
    def __init__(self, chat: OllamaChat) -> None:
        self._chat = chat

    @property
    def model_name(self) -> str:
        return self._chat.model_name

    def find_matching_tags(self, product_name: str, tag_names: tuple[str, ...]) -> tuple[int, ...]:
        if not tag_names:
            raise ValueError("tag_names must not be empty")
        prompt = build_classification_prompt(product_name, tag_names)
        schema = build_classification_schema()
        content = self._ask(prompt, schema)
        return _read_choices(content, len(tag_names))

    def _ask(self, prompt: str, schema: dict[str, object]) -> str:
        try:
            return self._chat.ask_structured(prompt, schema)
        except OllamaUnavailableError as error:
            raise IngredientClassifierUnavailableError(str(error)) from error
        except OllamaContractError as error:
            raise IngredientClassifierContractError(str(error)) from error


def _read_choices(content: str, tag_count: int) -> tuple[int, ...]:
    try:
        body = json.loads(content)
    except json.JSONDecodeError as error:
        raise IngredientClassifierContractError("The model answer is not JSON.") from error
    numbers = body.get("tags") if isinstance(body, dict) else None
    if not isinstance(numbers, list):
        raise IngredientClassifierContractError("The model answer has no tag list.")
    choices: list[int] = []
    for number in numbers:
        if not isinstance(number, int) or isinstance(number, bool) or not 1 <= number <= tag_count:
            raise IngredientClassifierContractError(f"Unknown tag number {number!r}.")
        choices.append(number - 1)
    return tuple(sorted(set(choices)))
