from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from households.application.use_cases.analyze_unmatched_ingredients import (
    AnalyzeUnmatchedIngredients,
)
from households.composition import (
    build_alias_proposal_repository,
    build_household_repository,
    build_product_repository,
)
from households.domain.alias_analysis import AliasAnalysisReport
from households.domain.alias_proposal_state import AliasProposalState
from households.infrastructure.recipes_recipe_requirement_reader import (
    RecipesRecipeRequirementReader,
)
from households.models import (
    Household,
    HouseholdMembership,
    TagProposal,
    IngredientTag,
    Product,
    ProductTag,
)
from households.tests.alias_fakes import FakeIngredientMatcher, UnavailableIngredientMatcher
from inventory.composition import build_get_household_inventory
from inventory.models import InventoryItem
from recipes.domain.matching import find_matching_item
from recipes.models import Recipe, RecipeIngredient, RecipeStep
from shared.text import normalize_text

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def maria() -> User:
    return User.objects.create_user(username="maria", password="Ma-Kota-1234")


@pytest.fixture
def outsider() -> User:
    return User.objects.create_user(username="outsider", password="Ma-Psa-1234")


@pytest.fixture
def household(maria: User) -> Household:
    created = Household.objects.create(name="Jugosłowiańska")
    HouseholdMembership.objects.create(household=created, user=maria)
    return created


@pytest.fixture
def eggs(household: Household) -> Product:
    return Product.objects.create(
        household=household,
        name="Jaja ściółkowe (opakowanie)",
        normalized_name=normalize_text("Jaja ściółkowe (opakowanie)"),
        default_unit_code="szt",
        is_food=True,
    )


@pytest.fixture
def buttermilk(household: Household) -> Product:
    return Product.objects.create(
        household=household,
        name="Maślanka naturalna",
        normalized_name=normalize_text("Maślanka naturalna"),
        default_unit_code="l",
        is_food=True,
    )


@pytest.fixture
def pancakes(maria: User) -> Recipe:
    recipe = Recipe.objects.create(
        name="Naleśniki",
        description="",
        servings=4,
        preparation_time_minutes=10,
        cooking_time_minutes=15,
        difficulty="easy",
        created_by=maria,
    )
    RecipeStep.objects.create(recipe=recipe, position=1, text="Wymieszać.")
    RecipeIngredient.objects.create(
        recipe=recipe,
        name="jajko",
        normalized_name=normalize_text("jajko"),
        unit_code="szt",
        quantity=Decimal("2"),
    )
    return recipe


def _analyze(matcher: FakeIngredientMatcher, limit: int = 20) -> AliasAnalysisReport:
    return _build(matcher, limit).execute(NOW, False)


def _build(
    matcher: FakeIngredientMatcher | UnavailableIngredientMatcher, limit: int
) -> AnalyzeUnmatchedIngredients:
    return AnalyzeUnmatchedIngredients(
        build_household_repository(),
        build_product_repository(),
        RecipesRecipeRequirementReader(),
        build_alias_proposal_repository(),
        matcher,
        limit,
    )


def test_a_proposal_is_created_for_an_unmatched_requirement(
    household: Household, eggs: Product, pancakes: Recipe
) -> None:
    matcher = FakeIngredientMatcher({"jajko": eggs.name})

    report = _analyze(matcher)

    assert report.question_count == 1
    assert report.failure is None
    row = TagProposal.objects.get()
    assert row.household_id == household.pk
    assert row.product_id == eggs.pk
    assert row.requirement_name == "jajko"
    assert row.state == AliasProposalState.PENDING


def test_running_twice_creates_no_duplicate_proposal(eggs: Product, pancakes: Recipe) -> None:
    matcher = FakeIngredientMatcher({"jajko": eggs.name})

    _analyze(matcher)
    second = _analyze(matcher)

    assert TagProposal.objects.count() == 1
    assert second.question_count == 0
    assert len(matcher.questions) == 1


def test_a_rejected_pair_is_never_proposed_again(eggs: Product, pancakes: Recipe) -> None:
    matcher = FakeIngredientMatcher({"jajko": eggs.name})
    _analyze(matcher)
    TagProposal.objects.update(state=AliasProposalState.REJECTED)

    report = _analyze(matcher)

    assert report.question_count == 0
    assert TagProposal.objects.count() == 1


def test_an_already_aliased_requirement_is_skipped(eggs: Product, pancakes: Recipe) -> None:
    tag = IngredientTag.objects.create(name="jajko", normalized_name="jajko")
    ProductTag.objects.create(product=eggs, ingredient_tag=tag, is_verified=True)
    matcher = FakeIngredientMatcher({"jajko": eggs.name})

    report = _analyze(matcher)

    assert report.question_count == 0
    assert matcher.questions == []
    assert TagProposal.objects.count() == 0


def test_a_household_without_unmatched_requirements_is_not_asked_about(
    household: Household, pancakes: Recipe
) -> None:
    matcher = FakeIngredientMatcher({})

    report = _analyze(matcher)

    assert matcher.questions == []
    assert report.question_count == 0


def test_the_question_cap_is_respected(
    household: Household, eggs: Product, buttermilk: Product, maria: User, pancakes: Recipe
) -> None:
    RecipeIngredient.objects.create(
        recipe=pancakes,
        name="masło",
        normalized_name=normalize_text("masło"),
        unit_code="g",
        quantity=Decimal("30"),
    )
    matcher = FakeIngredientMatcher({"jajko": eggs.name})

    report = _build(matcher, 1).execute(NOW, False)

    assert report.question_count == 1
    assert report.limit_reached is True
    assert len(matcher.questions) == 1


def test_dry_run_writes_nothing(eggs: Product, pancakes: Recipe) -> None:
    matcher = FakeIngredientMatcher({"jajko": eggs.name})

    report = _build(matcher, 20).execute(NOW, True)

    assert len(report.households[0].proposals) == 1
    assert TagProposal.objects.count() == 0


def test_a_provider_failure_is_reported_without_corrupting_state(
    eggs: Product, pancakes: Recipe
) -> None:
    report = _build(UnavailableIngredientMatcher(), 20).execute(NOW, False)

    assert report.failure is not None
    assert "IngredientMatcherUnavailable" in report.failure
    assert TagProposal.objects.count() == 0


def test_accepting_creates_the_alias_and_makes_the_ingredient_match(
    api_client: APIClient, maria: User, household: Household, eggs: Product, pancakes: Recipe
) -> None:
    InventoryItem.objects.create(
        household=household, product=eggs, unit_code="szt", quantity=Decimal("10")
    )
    _analyze(FakeIngredientMatcher({"jajko": eggs.name}))
    proposal = TagProposal.objects.get()
    inventory = build_get_household_inventory().execute(maria.pk, household.pk)
    assert find_matching_item("jajko", inventory) is None

    api_client.force_login(maria)
    response = api_client.post(f"/api/households/tag-proposals/{proposal.pk}/accept/")

    assert response.status_code == 200
    assert response.data["state"] == "accepted"
    assert ProductTag.objects.filter(product=eggs, ingredient_tag__normalized_name="jajko").exists()
    refreshed = build_get_household_inventory().execute(maria.pk, household.pk)
    matched = find_matching_item("jajko", refreshed)
    assert matched is not None
    assert matched.product_id == eggs.pk


def test_rejecting_marks_the_proposal_rejected(
    api_client: APIClient, maria: User, eggs: Product, pancakes: Recipe
) -> None:
    _analyze(FakeIngredientMatcher({"jajko": eggs.name}))
    proposal = TagProposal.objects.get()
    api_client.force_login(maria)

    response = api_client.post(f"/api/households/tag-proposals/{proposal.pk}/reject/")

    assert response.status_code == 200
    assert response.data["state"] == "rejected"
    assert ProductTag.objects.count() == 0


def test_a_member_lists_pending_proposals(
    api_client: APIClient, maria: User, household: Household, eggs: Product, pancakes: Recipe
) -> None:
    _analyze(FakeIngredientMatcher({"jajko": eggs.name}))
    api_client.force_login(maria)

    response = api_client.get(f"/api/households/{household.pk}/tag-proposals/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["requirement_name"] == "jajko"
    assert response.data[0]["product_name"] == eggs.name


def test_a_non_member_cannot_list_accept_or_reject(
    api_client: APIClient,
    outsider: User,
    household: Household,
    eggs: Product,
    pancakes: Recipe,
) -> None:
    _analyze(FakeIngredientMatcher({"jajko": eggs.name}))
    proposal = TagProposal.objects.get()
    api_client.force_login(outsider)

    listed = api_client.get(f"/api/households/{household.pk}/tag-proposals/")
    accepted = api_client.post(f"/api/households/tag-proposals/{proposal.pk}/accept/")
    rejected = api_client.post(f"/api/households/tag-proposals/{proposal.pk}/reject/")

    assert listed.status_code == 403
    assert accepted.status_code == 403
    assert rejected.status_code == 403
    assert ProductTag.objects.count() == 0
    assert TagProposal.objects.get().state == AliasProposalState.PENDING
