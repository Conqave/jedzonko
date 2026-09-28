from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime

from catalog.application.ports.candidate_repository import CandidateRepository
from catalog.application.ports.ingredient_classifier import IngredientClassifier
from catalog.application.ports.ingredient_references import IngredientReferences
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.candidate import CandidateStatus, IngredientNameCandidate
from catalog.domain.classification import ProductClassification
from catalog.domain.ingredient import (
    Ingredient,
    IngredientName,
    IngredientNameKind,
    IngredientNameSource,
)
from catalog.domain.names import CatalogName
from catalog.domain.product import Product, ProductListing, ProductPackage
from catalog.domain.product_ingredient import ProductIngredient, ProductIngredientStatus
from shared.household_membership import HouseholdMembershipReader
from shared.transactions import TransactionManager


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
        self._next_id = 1

    def find(self, ingredient_id: int) -> Ingredient | None:
        return self.ingredients.get(ingredient_id)

    def find_many(self, ingredient_ids: set[int]) -> dict[int, Ingredient]:
        return {key: value for key, value in self.ingredients.items() if key in ingredient_ids}

    def find_by_normalized_name(self, normalized_name: str) -> Ingredient | None:
        for name in self.names:
            if name.normalized_name == normalized_name:
                return self.ingredients[name.ingredient_id]
        return None

    def find_by_normalized_names(self, normalized_names: set[str]) -> dict[str, Ingredient]:
        return {
            name.normalized_name: self.ingredients[name.ingredient_id]
            for name in self.names
            if name.normalized_name in normalized_names
        }

    def search(self, normalized_query: str, limit: int) -> list[Ingredient]:
        found = {
            name.ingredient_id for name in self.names if normalized_query in name.normalized_name
        }
        ordered = sorted((self.ingredients[each] for each in found), key=lambda item: item.name)
        return ordered[:limit]

    def list_names(self) -> list[IngredientName]:
        return list(self.names)

    def create(self, name: CatalogName, source: IngredientNameSource) -> Ingredient:
        ingredient = Ingredient(id=self._next_id, name=name.name)
        self._next_id += 1
        self.ingredients[ingredient.id] = ingredient
        self.add_name(ingredient.id, name, IngredientNameKind.CANONICAL, source)
        return ingredient

    def add_name(
        self,
        ingredient_id: int,
        name: CatalogName,
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

    def move_names_as_aliases(self, source_id: int, target_id: int) -> None:
        self.names = [
            (
                replace(name, ingredient_id=target_id, kind=IngredientNameKind.ALIAS)
                if name.ingredient_id == source_id
                else name
            )
            for name in self.names
        ]

    def delete(self, ingredient_id: int) -> None:
        if any(name.ingredient_id == ingredient_id for name in self.names):
            raise AssertionError("Names would cascade away; a merge moves them first.")
        del self.ingredients[ingredient_id]


class FakeProductRepository(ProductRepository):
    def __init__(self) -> None:
        self.products: dict[int, tuple[Product, str]] = {}
        self.confirmed: dict[int, int] = {}
        self._next_id = 1

    def add(self, household_id: int, name: str, is_food: bool = True) -> Product:
        text = CatalogName.parse(name)
        return self.create(household_id, text, "szt", is_food, None)

    def find(self, product_id: int) -> Product | None:
        entry = self.products.get(product_id)
        return None if entry is None else entry[0]

    def find_by_name(self, household_id: int, normalized_name: str) -> Product | None:
        for product, normalized in self.products.values():
            if product.household_id == household_id and normalized == normalized_name:
                return product
        return None

    def list_listings(
        self, household_id: int, normalized_search: str | None
    ) -> list[ProductListing]:
        return [
            ProductListing(
                product=product,
                ingredient_id=self.confirmed.get(product.id),
                ingredient_name=None,
                open_proposal_count=0,
            )
            for product, normalized in self.products.values()
            if product.household_id == household_id
            and (normalized_search is None or normalized_search in normalized)
        ]

    def list_for_household(self, household_id: int) -> list[Product]:
        return [
            product for product, _ in self.products.values() if product.household_id == household_id
        ]

    def list_unclassified(self) -> list[Product]:
        return [
            product
            for product, _ in self.products.values()
            if product.is_food and product.id not in self.confirmed
        ]

    def create(
        self,
        household_id: int,
        name: CatalogName,
        default_unit_code: str,
        is_food: bool,
        package: ProductPackage | None,
    ) -> Product:
        product = Product(
            id=self._next_id,
            household_id=household_id,
            name=name.name,
            default_unit_code=default_unit_code,
            is_food=is_food,
            package=package,
        )
        self._next_id += 1
        self.products[product.id] = (product, name.normalized_name)
        return product

    def update(self, product_id: int, name: CatalogName, package: ProductPackage | None) -> Product:
        product, _ = self.products[product_id]
        updated = replace(product, name=name.name, package=package)
        self.products[product_id] = (updated, name.normalized_name)
        return updated


@dataclass
class FakeProduct:
    household_id: int
    links: dict[int, ProductIngredient] = field(default_factory=dict)


class FakeProductClassificationRepository(ProductClassificationRepository):

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

    def list_links_to(self, ingredient_id: int) -> list[ProductIngredient]:
        return [
            link
            for product in self.products.values()
            for link in product.links.values()
            if link.ingredient_id == ingredient_id
        ]

    def delete(self, product_id: int, ingredient_id: int) -> None:
        del self.products[product_id].links[ingredient_id]


class FakeCandidateRepository(CandidateRepository):
    def __init__(self) -> None:
        self.candidates: dict[int, IngredientNameCandidate] = {}

    def find(self, candidate_id: int) -> IngredientNameCandidate | None:
        return self.candidates.get(candidate_id)

    def existing_normalized_names(self, normalized_names: set[str]) -> set[str]:
        return {
            candidate.normalized_name
            for candidate in self.candidates.values()
            if candidate.normalized_name in normalized_names
        }

    def create(self, name: CatalogName, source: IngredientNameSource) -> IngredientNameCandidate:
        candidate = IngredientNameCandidate(
            id=len(self.candidates) + 1,
            name=name.name,
            normalized_name=name.normalized_name,
            source=source,
            status=CandidateStatus.PENDING,
            decided_at=None,
        )
        self.candidates[candidate.id] = candidate
        return candidate

    def decide(self, candidate_id: int, status: CandidateStatus, decided_at: datetime) -> None:
        candidate = self.candidates[candidate_id]
        self.candidates[candidate_id] = replace(candidate, status=status, decided_at=decided_at)


class FakeIngredientReferences(IngredientReferences):
    def __init__(self) -> None:
        self.reassigned: list[tuple[int, int]] = []

    def reassign(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        self.reassigned.append((source_ingredient_id, target_ingredient_id))


class FakeIngredientClassifier(IngredientClassifier):

    def __init__(self, answers: dict[str, str | None]) -> None:
        self._answers = answers
        self.questions: list[tuple[str, tuple[str, ...]]] = []

    @property
    def model_name(self) -> str:
        return "fake-model"

    def find_matching_ingredient(
        self, product_name: str, ingredient_names: tuple[str, ...]
    ) -> int | None:
        self.questions.append((product_name, ingredient_names))
        wanted = self._answers[product_name]
        if wanted is None:
            return None
        return ingredient_names.index(wanted)


class FakeHouseholdMembershipReader(HouseholdMembershipReader):
    def __init__(self, memberships: set[tuple[int, int]]) -> None:
        self._memberships = memberships

    def is_member(self, user_id: int, household_id: int) -> bool:
        return (user_id, household_id) in self._memberships
