from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field

from catalog.application.ports.household_membership_reader import HouseholdMembershipReader
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.application.ports.transaction_manager import TransactionManager
from catalog.domain.classification import ProductClassification
from catalog.domain.ingredient import (
    Ingredient,
    IngredientName,
    IngredientNameKind,
    IngredientNameSource,
)
from catalog.domain.names import IngredientNameText
from catalog.domain.product_ingredient import ProductIngredient, ProductIngredientStatus


class FakeTransactionManager(TransactionManager):
    def __init__(self) -> None:
        self.depth = 0
        self.opened = 0

    def atomic(self) -> AbstractContextManager[None]:
        return self._atomic()

    @contextmanager
    def _atomic(self) -> Iterator[None]:
        self.depth += 1
        self.opened += 1
        try:
            yield
        finally:
            self.depth -= 1


class FakeIngredientRepository(IngredientRepository):
    def __init__(self) -> None:
        self.ingredients: dict[int, Ingredient] = {}
        self.names: list[IngredientName] = []

    def find(self, ingredient_id: int) -> Ingredient | None:
        return self.ingredients.get(ingredient_id)

    def find_by_normalized_name(self, normalized_name: str) -> Ingredient | None:
        for name in self.names:
            if name.normalized_name == normalized_name:
                return self.ingredients[name.ingredient_id]
        return None

    def create(self, name: IngredientNameText, source: IngredientNameSource) -> Ingredient:
        ingredient = Ingredient(id=len(self.ingredients) + 1, name=name.name)
        self.ingredients[ingredient.id] = ingredient
        self.add_name(ingredient.id, name, IngredientNameKind.CANONICAL, source)
        return ingredient

    def add_name(
        self,
        ingredient_id: int,
        name: IngredientNameText,
        kind: IngredientNameKind,
        source: IngredientNameSource,
    ) -> IngredientName:
        if any(existing.normalized_name == name.normalized_name for existing in self.names):
            raise AssertionError("Unique constraint on the normalized name violated.")
        entry = IngredientName(
            ingredient_id=ingredient_id,
            name=name.name,
            normalized_name=name.normalized_name,
            kind=kind,
            source=source,
        )
        self.names.append(entry)
        return entry


@dataclass
class FakeProduct:
    household_id: int
    links: dict[int, ProductIngredient] = field(default_factory=dict)


class FakeProductClassificationRepository(ProductClassificationRepository):
    """Applies changes one by one and enforces the database invariants after each of them."""

    def __init__(self, transactions: FakeTransactionManager) -> None:
        self.products: dict[int, FakeProduct] = {}
        self.saved: list[ProductIngredient] = []
        self._transactions = transactions

    def add_product(self, product_id: int, household_id: int) -> None:
        self.products[product_id] = FakeProduct(household_id=household_id)

    def find(self, product_id: int) -> ProductClassification | None:
        product = self.products.get(product_id)
        if product is None:
            return None
        return ProductClassification(
            product_id=product_id,
            household_id=product.household_id,
            links=tuple(product.links.values()),
        )

    def save(self, changes: tuple[ProductIngredient, ...]) -> None:
        if self._transactions.depth < 1:
            raise AssertionError("Classification changes must be saved inside a transaction.")
        for change in changes:
            links = self.products[change.product_id].links
            links[change.ingredient_id] = change
            confirmed = [
                link for link in links.values() if link.status is ProductIngredientStatus.CONFIRMED
            ]
            if len(confirmed) > 1:
                raise AssertionError("Unique constraint on the confirmed product violated.")
            self.saved.append(change)

    def list_confirmed(self, household_id: int) -> dict[int, int]:
        return {
            product_id: link.ingredient_id
            for product_id, product in self.products.items()
            if product.household_id == household_id
            for link in product.links.values()
            if link.status is ProductIngredientStatus.CONFIRMED
        }


class FakeHouseholdMembershipReader(HouseholdMembershipReader):
    def __init__(self, memberships: set[tuple[int, int]]) -> None:
        self._memberships = memberships

    def is_member(self, user_id: int, household_id: int) -> bool:
        return (user_id, household_id) in self._memberships
