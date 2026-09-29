from catalog.application.use_cases.list_tags import ListTags
from recipes.application.ports.tag_vocabulary import TagVocabulary
from recipes.domain.external_line import IngredientChoice


class CatalogTagVocabulary(TagVocabulary):
    def __init__(self, list_tags: ListTags) -> None:
        self._list_tags = list_tags

    def list_tags(self) -> tuple[IngredientChoice, ...]:
        tags = self._list_tags.execute()
        return tuple(IngredientChoice(id=tag.id, name=tag.name) for tag in tags)
