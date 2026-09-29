from dataclasses import dataclass

from catalog.domain.ingredient import Ingredient
from shared.text import normalize_text

STEM_LENGTH = 4


@dataclass(frozen=True, slots=True)
class TagGroup:
    canonical: int
    members: tuple[int, ...]


def find_stem_clusters(tags: tuple[Ingredient, ...]) -> tuple[tuple[Ingredient, ...], ...]:
    clusters: dict[tuple[str, ...], list[Ingredient]] = {}
    for tag in tags:
        words = normalize_text(tag.name).split()
        stems = tuple(sorted(word[:STEM_LENGTH] for word in words))
        clusters.setdefault(stems, []).append(tag)
    return tuple(tuple(cluster) for cluster in clusters.values() if len(cluster) > 1)
