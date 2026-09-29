import json

import httpx
import pytest

from catalog.application.errors import IngredientClassifierContractError
from catalog.application.ports.tag_unifier import TagUnifier
from catalog.application.use_cases.list_tags import ListTags
from catalog.application.use_cases.merge_ingredients import MergeIngredients
from catalog.application.use_cases.unify_tags import UnifyTags
from catalog.domain.ingredient import IngredientNameKind, IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.domain.tag_duplicates import TagGroup, find_stem_clusters
from catalog.infrastructure.providers.ollama.tag_unifier import OllamaTagUnifier
from catalog.tests.fakes import (
    FakeIngredientLineRepository,
    FakeIngredientReferences,
    FakeIngredientRepository,
    FakeProductClassificationRepository,
    FakeTransactionManager,
)
from shared.infrastructure.ollama_chat import OllamaChat, OllamaSettings

NAMES = ("cebula", "cebula czerwona", "czerwona cebula", "ogórek", "ogórki", "maślanka")


class ScriptedUnifier(TagUnifier):
    def __init__(self, answers: dict[tuple[str, ...], tuple[tuple[str, tuple[str, ...]], ...]]):
        self._answers = answers
        self.questions: list[tuple[str, ...]] = []

    def find_same_ingredients(self, tag_names: tuple[str, ...]) -> tuple[TagGroup, ...]:
        self.questions.append(tag_names)
        groups = []
        for canonical, members in self._answers.get(tag_names, ()):
            positions = tuple(sorted(tag_names.index(member) for member in members))
            groups.append(TagGroup(canonical=tag_names.index(canonical), members=positions))
        return tuple(groups)


class Tags:
    def __init__(self) -> None:
        self.ingredients = FakeIngredientRepository()
        transactions = FakeTransactionManager()
        for name in NAMES:
            self.ingredients.create(CatalogName.parse(name), IngredientNameSource.ANIA_GOTUJE)
        self.merge = MergeIngredients(
            self.ingredients,
            FakeProductClassificationRepository(transactions),
            (FakeIngredientReferences(),),
            FakeIngredientLineRepository({}),
            transactions,
        )

    def canonical_names(self) -> list[str]:
        names = self.ingredients.list_names()
        return sorted(name.name for name in names if name.kind is IngredientNameKind.CANONICAL)

    def alias_names(self) -> list[str]:
        names = self.ingredients.list_names()
        return sorted(name.name for name in names if name.kind is IngredientNameKind.ALIAS)


def test_similar_tags_are_clustered_by_stems_regardless_of_word_order() -> None:
    tags = Tags()

    clusters = find_stem_clusters(ListTags(tags.ingredients).execute())

    assert sorted(tuple(tag.name for tag in cluster) for cluster in clusters) == [
        ("cebula czerwona", "czerwona cebula"),
        ("ogórek", "ogórki"),
    ]


def test_confirmed_duplicates_are_merged_into_the_main_name_as_aliases() -> None:
    tags = Tags()
    unifier = ScriptedUnifier(
        {
            ("cebula czerwona", "czerwona cebula"): (
                ("czerwona cebula", ("cebula czerwona", "czerwona cebula")),
            ),
            ("ogórek", "ogórki"): (("ogórek", ("ogórek", "ogórki")),),
        }
    )

    run = UnifyTags(ListTags(tags.ingredients), unifier, tags.merge).execute(dry_run=False)

    assert [merge.target.name for merge in run.merges] == ["czerwona cebula", "ogórek"]
    assert tags.canonical_names() == ["cebula", "czerwona cebula", "maślanka", "ogórek"]
    assert tags.alias_names() == ["cebula czerwona", "ogórki"]


def test_a_dry_run_merges_nothing() -> None:
    tags = Tags()
    unifier = ScriptedUnifier({("ogórek", "ogórki"): (("ogórek", ("ogórek", "ogórki")),)})

    run = UnifyTags(ListTags(tags.ingredients), unifier, tags.merge).execute(dry_run=True)

    assert len(run.merges) == 1
    assert len(tags.canonical_names()) == len(NAMES)


def _unifier(content: str) -> OllamaTagUnifier:
    body = {"message": {"role": "assistant", "content": content}, "done_reason": "stop"}
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )
    settings = OllamaSettings("http://192.0.2.1:11434", "gpt-oss:20b-128k", "high", 10, 256)
    return OllamaTagUnifier(OllamaChat(client, settings))


def test_the_model_answer_names_tags_and_unknown_names_are_ignored() -> None:
    answer = {
        "groups": [
            {"canonical": "ogórek", "members": ["ogórek", "ogórki", "ogóreczki"]},
            {"canonical": "brak", "members": ["cebula"]},
            {"canonical": "cebula", "members": ["cebula"]},
        ]
    }

    groups = _unifier(json.dumps(answer)).find_same_ingredients(NAMES)

    assert groups == (TagGroup(canonical=3, members=(3, 4)),)


def test_a_tag_joins_only_one_group() -> None:
    answer = {
        "groups": [
            {"canonical": "ogórek", "members": ["ogórki"]},
            {"canonical": "ogórki", "members": ["ogórki", "maślanka"]},
        ]
    }

    groups = _unifier(json.dumps(answer)).find_same_ingredients(NAMES)

    assert groups == (TagGroup(canonical=3, members=(3, 4)),)


def test_an_answer_that_is_not_json_breaks_the_contract() -> None:
    with pytest.raises(IngredientClassifierContractError):
        _unifier("nie wiem").find_same_ingredients(NAMES)


class FailingWholeListUnifier(ScriptedUnifier):
    def find_same_ingredients(self, tag_names: tuple[str, ...]) -> tuple[TagGroup, ...]:
        if len(tag_names) == len(NAMES):
            raise IngredientClassifierContractError("Ollama stopped at the output token limit.")
        return super().find_same_ingredients(tag_names)


def test_a_failed_pass_is_reported_and_the_other_passes_still_run() -> None:
    tags = Tags()
    unifier = FailingWholeListUnifier({("ogórek", "ogórki"): (("ogórek", ("ogórek", "ogórki")),)})

    run = UnifyTags(ListTags(tags.ingredients), unifier, tags.merge).execute(dry_run=True)

    assert [merge.target.name for merge in run.merges] == ["ogórek"]
    assert run.skipped == ("6 tag(s) from cebula: Ollama stopped at the output token limit.",)
