from datetime import datetime

from households.application.ports.alias_proposal_repository import AliasProposalRepository
from households.application.ports.household_repository import HouseholdRepository
from households.application.ports.ingredient_matcher import (
    IngredientMatcher,
    IngredientMatcherError,
)
from households.application.ports.product_repository import ProductRepository
from households.application.ports.recipe_requirement_reader import RecipeRequirementReader
from households.domain.alias_analysis import AliasAnalysisReport, HouseholdAliasAnalysis
from households.domain.alias_proposal import AliasProposal
from households.domain.alias_proposal_state import AliasProposalState
from households.domain.ingredient_requirement import IngredientRequirement
from households.domain.models import HouseholdSummary
from households.domain.product_names import ProductNames
from households.domain.unmatched_ingredients import find_unmatched_requirements


class AnalyzeUnmatchedIngredients:
    def __init__(
        self,
        household_repository: HouseholdRepository,
        product_repository: ProductRepository,
        requirement_reader: RecipeRequirementReader,
        proposal_repository: AliasProposalRepository,
        matcher: IngredientMatcher,
        question_limit: int,
    ) -> None:
        self._household_repository = household_repository
        self._product_repository = product_repository
        self._requirement_reader = requirement_reader
        self._proposal_repository = proposal_repository
        self._matcher = matcher
        self._question_limit = question_limit

    def execute(self, now: datetime, dry_run: bool) -> AliasAnalysisReport:
        requirements = self._requirement_reader.list_requirements()
        analyses: list[HouseholdAliasAnalysis] = []
        remaining = self._question_limit
        failure: str | None = None
        for household in self._household_repository.list_active_households():
            if remaining < 1 or failure is not None:
                break
            products = self._product_repository.list_product_names(household.id)
            unmatched = find_unmatched_requirements(requirements, products)
            pending = self._proposal_repository.list_pending_requirement_names(household.id)
            open_requirements = [
                requirement
                for requirement in unmatched
                if requirement.normalized_name not in pending
            ]
            if not open_requirements:
                analyses.append(self._empty_analysis(household, len(unmatched)))
                continue
            rejected = self._proposal_repository.list_rejected_pairs(household.id)
            asked = 0
            proposals: list[AliasProposal] = []
            for requirement in open_requirements:
                if remaining < 1:
                    break
                candidates = [
                    product
                    for product in products
                    if (requirement.normalized_name, product.id) not in rejected
                ]
                if not candidates:
                    continue
                remaining -= 1
                asked += 1
                try:
                    choice = self._matcher.find_matching_product(
                        requirement.name, tuple(product.name for product in candidates)
                    )
                except IngredientMatcherError as error:
                    failure = f"{type(error).__name__}: {error}"
                    break
                if choice is None:
                    continue
                proposals.append(
                    self._record(household.id, requirement, candidates[choice], now, dry_run)
                )
            analyses.append(
                HouseholdAliasAnalysis(
                    household_id=household.id,
                    household_name=household.name,
                    unmatched_requirement_count=len(unmatched),
                    question_count=asked,
                    proposals=tuple(proposals),
                )
            )
        used = self._question_limit - remaining
        return AliasAnalysisReport(
            households=tuple(analyses),
            question_count=used,
            question_limit=self._question_limit,
            limit_reached=remaining < 1,
            failure=failure,
        )

    def _record(
        self,
        household_id: int,
        requirement: IngredientRequirement,
        product: ProductNames,
        now: datetime,
        dry_run: bool,
    ) -> AliasProposal:
        if dry_run:
            return AliasProposal(
                id=0,
                household_id=household_id,
                requirement_name=requirement.name,
                normalized_requirement_name=requirement.normalized_name,
                product_id=product.id,
                product_name=product.name,
                model_name=self._matcher.model_name,
                created_at=now,
                state=AliasProposalState.PENDING,
            )
        return self._proposal_repository.create_proposal(
            household_id,
            requirement.name,
            requirement.normalized_name,
            product.id,
            self._matcher.model_name,
            now,
        )

    @staticmethod
    def _empty_analysis(
        household: HouseholdSummary, unmatched_count: int
    ) -> HouseholdAliasAnalysis:
        return HouseholdAliasAnalysis(
            household_id=household.id,
            household_name=household.name,
            unmatched_requirement_count=unmatched_count,
            question_count=0,
            proposals=(),
        )
