from dataclasses import dataclass

from catalog.application.ports.tag_unifier import TagUnifier
from catalog.application.use_cases.list_tags import ListTags
from catalog.application.use_cases.merge_ingredients import MergeIngredients
from catalog.domain.ingredient import Ingredient
from catalog.domain.tag_duplicates import TagGroup, find_stem_clusters


@dataclass(frozen=True, slots=True)
class TagMerge:
    target: Ingredient
    sources: tuple[Ingredient, ...]


@dataclass(frozen=True, slots=True)
class UnificationRun:
    merges: tuple[TagMerge, ...]


class UnifyTags:
    def __init__(
        self, list_tags: ListTags, unifier: TagUnifier, merge_ingredients: MergeIngredients
    ) -> None:
        self._list_tags = list_tags
        self._unifier = unifier
        self._merge_ingredients = merge_ingredients

    def execute(self, dry_run: bool) -> UnificationRun:
        tags = self._list_tags.execute()
        merges: list[TagMerge] = []
        merged_ids: set[int] = set()
        passes = (tags, *find_stem_clusters(tags))
        for candidates in passes:
            for merge in self._ask(candidates):
                ids = {merge.target.id, *(source.id for source in merge.sources)}
                if ids & merged_ids:
                    continue
                merged_ids |= ids
                merges.append(merge)
        if not dry_run:
            for merge in merges:
                self._apply(merge)
        return UnificationRun(merges=tuple(merges))

    def _ask(self, candidates: tuple[Ingredient, ...]) -> tuple[TagMerge, ...]:
        names = tuple(tag.name for tag in candidates)
        groups = self._unifier.find_same_ingredients(names)
        return tuple(_to_merge(candidates, group) for group in groups)

    def _apply(self, merge: TagMerge) -> None:
        for source in merge.sources:
            self._merge_ingredients.execute(source.id, merge.target.id)


def _to_merge(candidates: tuple[Ingredient, ...], group: TagGroup) -> TagMerge:
    target = candidates[group.canonical]
    sources = tuple(candidates[member] for member in group.members if member != group.canonical)
    return TagMerge(target=target, sources=sources)
