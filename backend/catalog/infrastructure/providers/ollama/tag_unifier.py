import json

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.application.ports.tag_unifier import TagUnifier
from catalog.domain.tag_duplicates import TagGroup
from shared.infrastructure.ollama_chat import (
    OllamaChat,
    OllamaContractError,
    OllamaUnavailableError,
)

UNIFICATION_OUTPUT_TOKENS = 32768

_INSTRUCTIONS = (
    "To są tagi składników kulinarnych z serwisu Ania Gotuje. Lista może zawierać "
    "duplikaty: ten sam składnik zapisany inaczej - inna liczba lub odmiana gramatyczna, inny "
    "szyk słów, zdrobnienie, synonim albo literówka („cebula czerwona” i „czerwona cebula”, "
    "„ogórek” i „ogórki”, „listek laurowy” i „liść laurowy”, „skrobia ziemniaczana” i „mąka "
    "ziemniaczana”).\n"
    "Znajdź wszystkie grupy tagów oznaczających dokładnie ten sam składnik, taki sam w sklepie. "
    "Rodzaje, gatunki i odmiany to różne tagi: mąka, mąka pszenna tortowa i mąka pszenna "
    "chlebowa; ryż i ryż jaśminowy; pomidory i pomidorki koktajlowe; cebula i cebula czerwona. "
    "Różne są też składniki tylko podobne: herbata i herbatniki, masło i maślanka, mąka i "
    "makaron, mleko i mleko kokosowe, oliwki i oliwa, śmietanka i śmietana, olejek i olej, "
    "maślak i maślanka, pieczarki i pieczywo. Nie łącz nazw, które nie są prawdziwymi "
    "słowami, z innymi tagami. W razie wątpliwości nie łącz.\n"
    "Dla każdej grupy wybierz nazwę główną: najprostszą i najczęściej używaną w przepisach. "
    "Używaj nazw dokładnie tak, jak są zapisane na liście."
)

_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "canonical": {"type": "string"},
                    "members": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["canonical", "members"],
            },
        }
    },
    "required": ["groups"],
}


class OllamaTagUnifier(TagUnifier):
    def __init__(self, chat: OllamaChat) -> None:
        self._chat = chat

    def find_same_ingredients(self, tag_names: tuple[str, ...]) -> tuple[TagGroup, ...]:
        listing = "\n".join(f"- {name}" for name in tag_names)
        prompt = (
            f"{_INSTRUCTIONS}\n\nTagi:\n{listing}\n\n"
            "Odpowiedz obiektem JSON z listą „groups”; każda grupa ma nazwę główną "
            "„canonical” i wszystkie nazwy grupy „members”. Tagi bez duplikatów pomiń."
        )
        try:
            content = self._chat.ask_structured_at_length(
                prompt, _SCHEMA, UNIFICATION_OUTPUT_TOKENS
            )
        except OllamaUnavailableError as error:
            raise IngredientClassifierUnavailableError(str(error)) from error
        except OllamaContractError as error:
            raise IngredientClassifierContractError(str(error)) from error
        return _read_groups(content, tag_names)


def _read_groups(content: str, tag_names: tuple[str, ...]) -> tuple[TagGroup, ...]:
    try:
        body = json.loads(content)
    except json.JSONDecodeError as error:
        raise IngredientClassifierContractError("The model answer is not JSON.") from error
    entries = body.get("groups") if isinstance(body, dict) else None
    if not isinstance(entries, list):
        raise IngredientClassifierContractError("The model answer has no group list.")
    positions = {name: position for position, name in enumerate(tag_names)}
    groups: list[TagGroup] = []
    seen: set[int] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise IngredientClassifierContractError("A group is not an object.")
        canonical = positions.get(str(entry.get("canonical")))
        raw_members = entry.get("members")
        if canonical is None or not isinstance(raw_members, list):
            continue
        members = {positions[name] for name in raw_members if name in positions} | {canonical}
        if len(members) < 2 or members & seen:
            continue
        seen |= members
        groups.append(TagGroup(canonical=canonical, members=tuple(sorted(members))))
    return tuple(groups)
