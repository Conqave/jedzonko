from abc import ABC, abstractmethod

from catalog.domain.tag_duplicates import TagGroup


class TagUnifier(ABC):
    @abstractmethod
    def find_same_ingredients(self, tag_names: tuple[str, ...]) -> tuple[TagGroup, ...]:
        raise NotImplementedError
