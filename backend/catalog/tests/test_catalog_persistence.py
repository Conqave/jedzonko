import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone

from catalog.models import (
    Ingredient,
    IngredientName,
    IngredientNameCandidate,
    Product,
    ProductIngredient,
)
from config.composition import container
from households.models import Household
from tests.factories import confirm_ingredient, make_ingredient, make_product

pytestmark = pytest.mark.django_db


def _link(product: Product, ingredient: Ingredient, status: str) -> ProductIngredient:
    decided_at = None if status == "proposed" else timezone.now()
    return ProductIngredient.objects.create(
        product=product,
        ingredient=ingredient,
        status=status,
        source="manual",
        decided_at=decided_at,
    )


def test_a_product_cannot_have_two_confirmed_ingredients(household_a: Household) -> None:
    product = make_product(household_a, "Jaja ściółkowe", "opak")
    eggs = make_ingredient("Jajka")
    butter = make_ingredient("Masło")
    _link(product, eggs, "confirmed")

    with pytest.raises(IntegrityError), transaction.atomic():
        _link(product, butter, "confirmed")


def test_a_product_may_keep_many_proposals_and_rejections(household_a: Household) -> None:
    product = make_product(household_a, "Mieszanka", "opak")
    for name in ["Słonecznik", "Sezam"]:
        _link(product, make_ingredient(name), "proposed")
    _link(product, make_ingredient("Dynia"), "rejected")

    assert ProductIngredient.objects.filter(product=product).count() == 3


def test_a_pair_is_recorded_once(household_a: Household) -> None:
    product = make_product(household_a, "Jaja", "szt")
    eggs = make_ingredient("Jajka")
    _link(product, eggs, "proposed")

    with pytest.raises(IntegrityError), transaction.atomic():
        _link(product, eggs, "rejected")


def test_an_ingredient_has_exactly_one_canonical_name() -> None:
    eggs = make_ingredient("Jajka")

    with pytest.raises(IntegrityError), transaction.atomic():
        IngredientName.objects.create(
            ingredient=eggs, name="Jaja", normalized_name="jaja", kind="canonical", source="manual"
        )


def test_a_normalized_name_belongs_to_one_ingredient() -> None:
    make_ingredient("Jajka")
    other = make_ingredient("Jaja")

    with pytest.raises(IntegrityError), transaction.atomic():
        IngredientName.objects.create(
            ingredient=other, name="jajka", normalized_name="jajka", kind="alias", source="manual"
        )


def test_a_model_proposal_must_name_its_model(household_a: Household) -> None:
    product = make_product(household_a, "Jaja", "szt")
    eggs = make_ingredient("Jajka")

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductIngredient.objects.create(
            product=product, ingredient=eggs, status="proposed", source="model"
        )


def test_an_ingredient_in_use_cannot_be_deleted(ala: User, household_a: Household) -> None:
    product = make_product(household_a, "Jaja", "szt")
    eggs = make_ingredient("Jajka")
    confirm_ingredient(ala, product, eggs)

    with pytest.raises(IntegrityError), transaction.atomic():
        Ingredient.objects.filter(pk=eggs.pk).delete()


def test_deleting_a_product_removes_its_classification(ala: User, household_a: Household) -> None:
    product = make_product(household_a, "Jaja", "szt")
    confirm_ingredient(ala, product, make_ingredient("Jajka"))

    Product.objects.filter(pk=product.pk).delete()

    assert not ProductIngredient.objects.exists()


def test_quarantined_names_never_resolve() -> None:
    IngredientNameCandidate.objects.create(
        name="Jajka", normalized_name="jajka", source="ania_gotuje", status="pending"
    )
    find_by_name = container().catalog.find_ingredient_by_name

    found = find_by_name.execute("jajka")

    assert found is None


def test_confirming_another_ingredient_demotes_the_first_in_the_database(
    ala: User, household_a: Household
) -> None:
    product = make_product(household_a, "Jaja", "szt")
    butter = make_ingredient("Masło")
    eggs = make_ingredient("Jajka")
    confirm_ingredient(ala, product, butter)

    confirm_ingredient(ala, product, eggs)

    statuses = dict(
        ProductIngredient.objects.filter(product=product).values_list("ingredient__name", "status")
    )
    assert statuses == {"Masło": "rejected", "Jajka": "confirmed"}
