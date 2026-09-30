import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import httpx


class OllamaUnavailableError(Exception):
    pass


class OllamaContractError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class OllamaSettings:
    base_url: str
    model: str
    think: str
    timeout_seconds: float
    max_output_tokens: int
    context_tokens: int
    max_context_tokens: int


CHARACTERS_PER_TOKEN_LOWER_BOUND = 3


def estimate_tokens_upper_bound(text: str) -> int:
    return -(-len(text) // CHARACTERS_PER_TOKEN_LOWER_BOUND)


class OllamaChat:
    def __init__(self, client: httpx.Client, settings: OllamaSettings) -> None:
        self._client = client
        self._url = settings.base_url.rstrip("/") + "/api/chat"
        self._model = settings.model
        self._think = settings.think
        self._max_output_tokens = settings.max_output_tokens
        self._max_context_tokens = settings.max_context_tokens
        self._context_tokens = settings.context_tokens

    @property
    def model_name(self) -> str:
        return self._model

    def ask_structured(self, prompt: str, response_schema: dict[str, object]) -> str:
        return self.ask_structured_at_length(prompt, response_schema, self._max_output_tokens)

    def ask_structured_at_length(
        self, prompt: str, response_schema: dict[str, object], max_output_tokens: int
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        required_tokens = self._required_tokens(messages, response_schema, max_output_tokens)
        context_tokens = self._select_context_tokens(required_tokens)
        payload: dict[str, object] = {
            "model": self._model,
            "stream": False,
            "think": self._think,
            "options": {"num_predict": max_output_tokens, "num_ctx": context_tokens},
            "messages": messages,
            "format": response_schema,
        }
        return self._send(payload)

    def _required_tokens(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, object],
        max_output_tokens: int,
    ) -> int:
        prompt_text = json.dumps(messages, ensure_ascii=False) + json.dumps(
            response_schema, ensure_ascii=False
        )
        prompt_tokens = estimate_tokens_upper_bound(prompt_text)
        return prompt_tokens + max_output_tokens

    def _select_context_tokens(self, required_tokens: int) -> int:
        if required_tokens > self._max_context_tokens:
            raise OllamaContractError(
                f"Ollama request needs about {required_tokens} tokens, "
                f"above the {self._max_context_tokens} token context."
            )
        if required_tokens > self._context_tokens:
            self._context_tokens = self._max_context_tokens
        return self._context_tokens

    def _send(self, payload: dict[str, object]) -> str:
        try:
            response = self._client.post(self._url, json=payload)
        except httpx.HTTPError as error:
            raise OllamaUnavailableError(f"Ollama request failed: {self._url}") from error
        if response.status_code >= httpx.codes.BAD_REQUEST:
            raise OllamaUnavailableError(f"Ollama responded {response.status_code}.")
        try:
            body = response.json()
        except json.JSONDecodeError as error:
            raise OllamaContractError("Ollama response is not valid JSON.") from error
        message = body.get("message") if isinstance(body, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise OllamaContractError("Ollama response has no message content.")
        if body.get("done_reason") == "length":
            raise OllamaContractError("Ollama stopped at the output token limit.")
        return content


@contextmanager
def open_ollama_chat(settings: OllamaSettings) -> Iterator[OllamaChat]:
    timeout = httpx.Timeout(settings.timeout_seconds)
    with httpx.Client(timeout=timeout) as client:
        yield OllamaChat(client, settings)
