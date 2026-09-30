from dataclasses import replace
from decimal import Decimal

from catalog.application.errors import IngredientNotFoundError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.conversions import PieceWeight
from catalog.domain.ingredient import Ingredient
from shared.transactions import TransactionManager


class SetTagPieceWeight:
    def __init__(self, ingredients: IngredientRepository, transactions: TransactionManager) -> None:
        self._ingredients = ingredients
        self._transactions = transactions

    def execute(self, ingredient_id: int, grams_per_piece: Decimal | None) -> Ingredient:
        piece_weight = None if grams_per_piece is None else PieceWeight.manual(grams_per_piece)
        with self._transactions.atomic():
            ingredient = self._ingredients.find(ingredient_id)
            if ingredient is None:
                raise IngredientNotFoundError
            self._ingredients.save_piece_weight(ingredient_id, piece_weight)
        return replace(ingredient, piece_weight=piece_weight)
