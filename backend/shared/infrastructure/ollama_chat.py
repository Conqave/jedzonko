import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import httpx


class OllamaError(Exception):
    pass


class OllamaUnavailableError(OllamaError):
    pass


class OllamaContractError(OllamaError):
    pass


@dataclass(frozen=True, slots=True)
class OllamaSettings:
    base_url: str
    model: str
    think: str
    timeout_seconds: float


class OllamaChat:
    def __init__(self, client: httpx.Client, settings: OllamaSettings) -> None:
        self._client = client
        self._url = settings.base_url.rstrip("/") + "/api/chat"
        self._model = settings.model
        self._think = settings.think

    @property
    def model_name(self) -> str:
        return self._model

    def ask(self, prompt: str) -> str:
        payload = self._build_payload(prompt)
        return self._send(payload)

    def ask_structured(self, prompt: str, response_schema: dict[str, object]) -> str:
        payload = self._build_payload(prompt)
        payload["format"] = response_schema
        return self._send(payload)

    def _build_payload(self, prompt: str) -> dict[str, object]:
        return {
            "model": self._model,
            "stream": False,
            "think": self._think,
            "messages": [{"role": "user", "content": prompt}],
        }

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
        return content


@contextmanager
def open_ollama_chat(settings: OllamaSettings) -> Iterator[OllamaChat]:
    timeout = httpx.Timeout(settings.timeout_seconds)
    with httpx.Client(timeout=timeout) as client:
        yield OllamaChat(client, settings)
