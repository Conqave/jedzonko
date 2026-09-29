import json

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
)
from catalog.application.ports.candidate_curator import CandidateCurator
from catalog.domain.curation import CurationDecision, CurationVerdict
from shared.infrastructure.ollama_chat import (
    OllamaChat,
    OllamaContractError,
    OllamaUnavailableError,
)

CURATION_OUTPUT_TOKENS = 32768

_INSTRUCTIONS = (
    "Budujemy jednolity słownik tagów składników kulinarnych. Poniżej jest obecny słownik oraz "
    "nowe nazwy zebrane z tagów przepisów serwisu Ania Gotuje; te nazwy bywają niespójne.\n"
    "Dla każdej nowej nazwy podejmij jedną decyzję:\n"
    "- „alias”: nazwa oznacza dokładnie składnik już obecny w słowniku, tylko zapisany inaczej "
    "(inna liczba lub odmiana, szyk słów, zdrobnienie, literówka, obcięta końcówka, synonim), "
    "np. „jajko” → „jajka”, „cebul” → „cebula”, „marchewka” → „marchew”, „koper” → „koperek”; "
    "wskaż wtedy nazwę ze słownika dokładnie tak, jak jest zapisana; jeśli dwie nowe nazwy "
    "to ten sam składnik, jedną oznacz „new_tag”, a drugą jako alias tej pierwszej;\n"
    "- „new_tag”: nazwa to składnik, który można kupić lub mieć w spiżarni, a w słowniku go nie "
    "ma; rodzaje i odmiany są osobnymi tagami (mąka pszenna tortowa, ryż jaśminowy, cebula "
    "czerwona);\n"
    "- „dismiss”: nazwa nie jest składnikiem, tylko potrawą, cechą przepisu albo określeniem "
    "(np. „dla dzieci”, „gofry”, „brownie”, „mielone”, „na zimno”)."
)

_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "decision": {
                        "type": "string",
                        "enum": [item.value for item in CurationDecision],
                    },
                    "alias_of": {"type": ["string", "null"]},
                },
                "required": ["name", "decision", "alias_of"],
            },
        }
    },
    "required": ["verdicts"],
}


class OllamaCandidateCurator(CandidateCurator):
    def __init__(self, chat: OllamaChat) -> None:
        self._chat = chat

    def curate(
        self, candidate_names: tuple[str, ...], tag_names: tuple[str, ...]
    ) -> tuple[CurationVerdict, ...]:
        dictionary = "\n".join(f"- {name}" for name in tag_names)
        candidates = "\n".join(f"- {name}" for name in candidate_names)
        prompt = (
            f"{_INSTRUCTIONS}\n\nSłownik:\n{dictionary}\n\nNowe nazwy:\n{candidates}\n\n"
            "Odpowiedz obiektem JSON z listą „verdicts”, po jednym wpisie na każdą nową nazwę: "
            "„name” (nowa nazwa bez zmian), „decision” i „alias_of” (nazwa ze słownika albo null)."
        )
        try:
            content = self._chat.ask_structured_at_length(prompt, _SCHEMA, CURATION_OUTPUT_TOKENS)
        except OllamaUnavailableError as error:
            raise IngredientClassifierUnavailableError(str(error)) from error
        except OllamaContractError as error:
            raise IngredientClassifierContractError(str(error)) from error
        return _read_verdicts(content, set(candidate_names), set(tag_names) | set(candidate_names))


def _read_verdicts(
    content: str, candidate_names: set[str], tag_names: set[str]
) -> tuple[CurationVerdict, ...]:
    try:
        body = json.loads(content)
    except json.JSONDecodeError as error:
        raise IngredientClassifierContractError("The model answer is not JSON.") from error
    entries = body.get("verdicts") if isinstance(body, dict) else None
    if not isinstance(entries, list):
        raise IngredientClassifierContractError("The model answer has no verdict list.")
    verdicts: list[CurationVerdict] = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("name") not in candidate_names:
            continue
        verdict = _to_verdict(entry, tag_names)
        if verdict is not None:
            verdicts.append(verdict)
    return tuple(verdicts)


def _to_verdict(entry: dict[str, object], tag_names: set[str]) -> CurationVerdict | None:
    name = str(entry["name"])
    decision_value = entry.get("decision")
    if decision_value not in {item.value for item in CurationDecision}:
        return None
    decision = CurationDecision(str(decision_value))
    if decision is not CurationDecision.ALIAS:
        return CurationVerdict(candidate=name, decision=decision, alias_of=None)
    alias_of = entry.get("alias_of")
    if not isinstance(alias_of, str) or alias_of not in tag_names:
        return None
    return CurationVerdict(candidate=name, decision=decision, alias_of=alias_of)
