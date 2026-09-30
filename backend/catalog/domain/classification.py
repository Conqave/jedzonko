from dataclasses import dataclass, replace
from datetime import datetime

from catalog.domain.errors import (
    ConfirmedProductIngredientDeletionError,
    InvalidProductClassificationError,
    InvalidProductIngredientTransitionError,
    ProductIngredientAlreadyRecordedError,
    ProductIngredientNotFoundError,
)
from catalog.domain.product_ingredient import (
    ProductIngredient,
    ProductIngredientSource,
    ProductIngredientStatus,
)


@dataclass(frozen=True, slots=True)
class ProductClassification:

    product_id: int
    household_id: int
    links: tuple[ProductIngredient, ...]

    def __post_init__(self) -> None:
        if any(link.product_id != self.product_id for link in self.links):
            raise InvalidProductClassificationError("A link belongs to another product.")
        ingredient_ids = [link.ingredient_id for link in self.links]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise InvalidProductClassificationError("An ingredient is recorded twice.")

    def confirmed(self) -> tuple[ProductIngredient, ...]:
        return tuple(
            link for link in self.links if link.status is ProductIngredientStatus.CONFIRMED
        )

    def rejected(self) -> tuple[ProductIngredient, ...]:
        return tuple(link for link in self.links if link.status is ProductIngredientStatus.REJECTED)

    def find(self, ingredient_id: int) -> ProductIngredient | None:
        for link in self.links:
            if link.ingredient_id == ingredient_id:
                return link
        return None

    def propose(self, ingredient_id: int, model_name: str, now: datetime) -> ProductIngredient:
        if self.find(ingredient_id) is not None:
            raise ProductIngredientAlreadyRecordedError
        return ProductIngredient(
            product_id=self.product_id,
            ingredient_id=ingredient_id,
            status=ProductIngredientStatus.PROPOSED,
            source=ProductIngredientSource.MODEL,
            model_name=model_name,
            proposed_at=now,
            decided_at=None,
        )

    def assign_from_model(
        self, ingredient_id: int, model_name: str, now: datetime
    ) -> ProductIngredient:
        if self.find(ingredient_id) is not None:
            raise ProductIngredientAlreadyRecordedError
        return ProductIngredient(
            product_id=self.product_id,
            ingredient_id=ingredient_id,
            status=ProductIngredientStatus.CONFIRMED,
            source=ProductIngredientSource.MODEL,
            model_name=model_name,
            proposed_at=now,
            decided_at=now,
        )

    def confirm(self, ingredient_id: int, now: datetime) -> tuple[ProductIngredient, ...]:
        existing = self.find(ingredient_id)
        if existing is not None and existing.status is ProductIngredientStatus.CONFIRMED:
            return ()
        changes: list[ProductIngredient] = []
        if existing is None:
            changes.append(
                ProductIngredient(
                    product_id=self.product_id,
                    ingredient_id=ingredient_id,
                    status=ProductIngredientStatus.CONFIRMED,
                    source=ProductIngredientSource.MANUAL,
                    model_name=None,
                    proposed_at=None,
                    decided_at=now,
                )
            )
        else:
            changes.append(
                replace(existing, status=ProductIngredientStatus.CONFIRMED, decided_at=now)
            )
        return tuple(changes)

    def reject(self, ingredient_id: int, now: datetime) -> ProductIngredient:
        existing = self.find(ingredient_id)
        if existing is None:
            raise ProductIngredientNotFoundError
        if existing.status is ProductIngredientStatus.REJECTED:
            raise InvalidProductIngredientTransitionError("The ingredient is already rejected.")
        return replace(existing, status=ProductIngredientStatus.REJECTED, decided_at=now)

    def forget(self, ingredient_id: int) -> ProductIngredient:
        existing = self.find(ingredient_id)
        if existing is None:
            raise ProductIngredientNotFoundError
        if existing.status is ProductIngredientStatus.CONFIRMED:
            raise ConfirmedProductIngredientDeletionError
        return existing

    def apply(self, changes: tuple[ProductIngredient, ...]) -> ProductClassification:
        links = {link.ingredient_id: link for link in self.links}
        for change in changes:
            links[change.ingredient_id] = change
        return replace(self, links=tuple(links.values()))
