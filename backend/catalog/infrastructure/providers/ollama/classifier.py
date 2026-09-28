import json
import re

import httpx

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.application.ports.ingredient_classifier import IngredientClassifier
from catalog.infrastructure.providers.ollama.prompt import build_classification_prompt

_INTEGER_PATTERN = re.compile(r"\d+")


class OllamaIngredientClassifier(IngredientClassifier):
    def __init__(self, client: httpx.Client, base_url: str, model: str, think: str | bool) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._think = think

    @property
    def model_name(self) -> str:
        return self._model

    def find_matching_ingredient(
        self, product_name: str, ingredient_names: tuple[str, ...]
    ) -> int | None:
        if not ingredient_names:
            raise ValueError("ingredient_names must not be empty")
        prompt = build_classification_prompt(product_name, ingredient_names)
        content = self._ask(prompt)
        return self._read_choice(content, len(ingredient_names))

    def _ask(self, prompt: str) -> str:
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model,
            "stream": False,
            "think": self._think,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = self._client.post(url, json=payload)
        except httpx.HTTPError as error:
            raise IngredientClassifierUnavailableError(f"Ollama request failed: {url}") from error
        if response.status_code >= httpx.codes.BAD_REQUEST:
            raise IngredientClassifierUnavailableError(
                f"Ollama responded {response.status_code} for {url}"
            )
        try:
            body = response.json()
        except json.JSONDecodeError as error:
            raise IngredientClassifierContractError("Ollama response is not valid JSON.") from error
        message = body.get("message") if isinstance(body, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise IngredientClassifierContractError("Ollama response has no message content.")
        return content

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
