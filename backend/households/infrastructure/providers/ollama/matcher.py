import json
import re

import httpx

from households.application.ports.ingredient_matcher import (
    IngredientMatcher,
    IngredientMatcherContractError,
    IngredientMatcherUnavailable,
)
from households.infrastructure.providers.ollama.prompt import build_matching_prompt

_INTEGER_PATTERN = re.compile(r"\d+")


class OllamaIngredientMatcher(IngredientMatcher):
    def __init__(self, client: httpx.Client, base_url: str, model: str, think: str | bool) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._think = think

    @property
    def model_name(self) -> str:
        return self._model

    def find_matching_product(
        self, ingredient_name: str, product_names: tuple[str, ...]
    ) -> int | None:
        if not product_names:
            raise ValueError("product_names must not be empty")
        content = self._ask(build_matching_prompt(ingredient_name, product_names))
        return self._read_choice(content, len(product_names))

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
            raise IngredientMatcherUnavailable(f"Ollama request failed: {url}") from error
        if response.status_code >= httpx.codes.BAD_REQUEST:
            raise IngredientMatcherUnavailable(f"Ollama responded {response.status_code} for {url}")
        try:
            body = response.json()
        except json.JSONDecodeError as error:
            raise IngredientMatcherContractError("Ollama response is not valid JSON.") from error
        if not isinstance(body, dict):
            raise IngredientMatcherContractError("Ollama response is not a JSON object.")
        try:
            message = body["message"]
        except KeyError as error:
            raise IngredientMatcherContractError("Ollama response has no 'message'.") from error
        if not isinstance(message, dict):
            raise IngredientMatcherContractError("Ollama 'message' is not a JSON object.")
        try:
            content = message["content"]
        except KeyError as error:
            raise IngredientMatcherContractError("Ollama message has no 'content'.") from error
        if not isinstance(content, str):
            raise IngredientMatcherContractError("Ollama 'content' is not text.")
        return content

    @staticmethod
    def _read_choice(content: str, product_count: int) -> int | None:
        numbers = _INTEGER_PATTERN.findall(content)
        if not numbers:
            raise IngredientMatcherContractError(
                f"Ollama answered without a number: {content[:200]!r}"
            )
        choice = int(numbers[-1])
        if choice == 0:
            return None
        if choice > product_count:
            raise IngredientMatcherContractError(
                f"Ollama answered {choice} for a list of {product_count} products."
            )
        return choice - 1
