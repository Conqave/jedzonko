from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from recipes.domain.external_line import LineInterpretation
from recipes.infrastructure.django_ingredient_line_repository import (
    DjangoIngredientLineRepository,
)
from recipes.infrastructure.django_recipe_repository import DjangoRecipeRepository
from recipes.models import ExternalIngredientLine
from tests.factories import make_ingredient

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 9, 29, 8, 0, tzinfo=UTC)


def test_interpretations_are_stored_once_per_line_and_replaced() -> None:
    eggs = make_ingredient("jajko")
    repository = DjangoIngredientLineRepository()
    first = LineInterpretation(ingredient_id=None, quantity=None, unit_code=None)
    second = LineInterpretation(ingredient_id=eggs.pk, quantity=Decimal("3"), unit_code="szt")

    repository.save_interpretations({"3 jajka": first}, "gpt-oss:20b-128k", NOW)
    repository.save_interpretations({"3 jajka": second}, "gpt-oss:20b-128k", NOW)

    assert repository.find_interpretations(("3 jajka", "mleko")) == {"3 jajka": second}
    assert ExternalIngredientLine.objects.count() == 1


def test_merging_ingredients_moves_line_interpretations() -> None:
    source = make_ingredient("jaja")
    target = make_ingredient("jajko")
    meaning = LineInterpretation(ingredient_id=source.pk, quantity=None, unit_code=None)
    DjangoIngredientLineRepository().save_interpretations({"jaja": meaning}, "model", NOW)

    DjangoRecipeRepository().reassign_ingredient(source.pk, target.pk)

    assert ExternalIngredientLine.objects.get().ingredient_id == target.pk


def test_the_database_requires_a_complete_amount() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        ExternalIngredientLine.objects.create(
            normalized_text="3 jajka", quantity=Decimal("3"), model_name="m", interpreted_at=NOW
        )
