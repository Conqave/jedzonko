from households.application.ports.product_alias_repository import ProductTagRepository
from households.models import IngredientTag, ProductTag
from shared.text import normalize_text


class DjangoProductTagRepository(ProductTagRepository):
    def create_tag(self, product_id: int, name: str, source: str = "ollama") -> None:
        tag = IngredientTag.objects.filter(
            normalized_name=normalize_text(name), source="ania_gotuje"
        ).first()
        if tag is None:
            return
        ProductTag.objects.get_or_create(
            product_id=product_id, ingredient_tag=tag,
            defaults={"source": source, "is_verified": True},
        )
