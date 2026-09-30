from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from catalog.application.ports.ingredient_references import IngredientReferences
from catalog.application.use_cases.add_ingredient_alias import AddIngredientAlias
from catalog.application.use_cases.analyze_product_ingredient import AnalyzeProductIngredient
from catalog.application.use_cases.confirm_product_ingredient import ConfirmProductIngredient
from catalog.application.use_cases.create_ingredient import CreateIngredient
from catalog.application.use_cases.create_product import CreateProduct
from catalog.application.use_cases.curate_candidates import CurateCandidates
from catalog.application.use_cases.decide_candidate import (
    AcceptCandidateAsAlias,
    AcceptCandidateAsIngredient,
    DismissCandidate,
)
from catalog.application.use_cases.delete_product import DeleteProduct
from catalog.application.use_cases.delete_product_ingredient import DeleteProductIngredient
from catalog.application.use_cases.delete_rejected_product_ingredients import (
    DeleteRejectedProductIngredients,
)
from catalog.application.use_cases.describe_household_products import DescribeHouseholdProducts
from catalog.application.use_cases.find_household_product import FindHouseholdProduct
from catalog.application.use_cases.find_ingredient_by_name import FindIngredientByName
from catalog.application.use_cases.find_ingredient_lines import FindIngredientLines
from catalog.application.use_cases.find_ingredients_by_names import FindIngredientsByNames
from catalog.application.use_cases.get_ingredients import GetIngredients
from catalog.application.use_cases.get_product_classification import GetProductClassification
from catalog.application.use_cases.get_product_nutrition import GetProductNutrition
from catalog.application.use_cases.import_ingredient_names import ImportIngredientNames
from catalog.application.use_cases.import_tag_calories import ImportTagCalories
from catalog.application.use_cases.import_tag_conversions import ImportTagConversions
from catalog.application.use_cases.interpret_ingredient_lines import InterpretIngredientLines
from catalog.application.use_cases.list_household_products import ListHouseholdProducts
from catalog.application.use_cases.list_measurement_units import ListMeasurementUnits
from catalog.application.use_cases.list_tags import ListTags
from catalog.application.use_cases.merge_ingredients import MergeIngredients
from catalog.application.use_cases.propose_ingredients_for_products import (
    ProposeIngredientsForProducts,
)
from catalog.application.use_cases.propose_product_ingredient import ProposeProductIngredient
from catalog.application.use_cases.reject_product_ingredient import RejectProductIngredient
from catalog.application.use_cases.search_ingredients import SearchIngredients
from catalog.application.use_cases.set_tag_calories import SetTagCalories
from catalog.application.use_cases.set_tag_density import SetTagDensity
from catalog.application.use_cases.set_tag_piece_weight import SetTagPieceWeight
from catalog.application.use_cases.split_alias import SplitAlias
from catalog.application.use_cases.unify_tags import UnifyTags
from catalog.application.use_cases.update_product import UpdateProduct
from catalog.infrastructure.django_candidate_repository import DjangoCandidateRepository
from catalog.infrastructure.django_ingredient_line_repository import (
    DjangoIngredientLineRepository,
)
from catalog.infrastructure.django_ingredient_repository import DjangoIngredientRepository
from catalog.infrastructure.django_product_classification_repository import (
    DjangoProductClassificationRepository,
)
from catalog.infrastructure.django_product_repository import DjangoProductRepository
from catalog.infrastructure.providers.ollama.candidate_curator import OllamaCandidateCurator
from catalog.infrastructure.providers.ollama.classifier import OllamaIngredientClassifier
from catalog.infrastructure.providers.ollama.line_interpreter import (
    OllamaIngredientLineInterpreter,
)
from catalog.infrastructure.providers.ollama.tag_unifier import OllamaTagUnifier
from shared.household_membership import HouseholdMembershipReader
from shared.infrastructure.ollama_chat import OllamaSettings, open_ollama_chat
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class CatalogModule:
    list_household_products: ListHouseholdProducts
    create_product: CreateProduct
    update_product: UpdateProduct
    delete_product: DeleteProduct
    find_household_product: FindHouseholdProduct
    describe_household_products: DescribeHouseholdProducts
    get_product_nutrition: GetProductNutrition
    list_measurement_units: ListMeasurementUnits
    create_ingredient: CreateIngredient
    add_ingredient_alias: AddIngredientAlias
    find_ingredient_by_name: FindIngredientByName
    find_ingredients_by_names: FindIngredientsByNames
    get_ingredients: GetIngredients
    search_ingredients: SearchIngredients
    list_tags: ListTags
    set_tag_calories: SetTagCalories
    import_tag_calories: ImportTagCalories
    set_tag_piece_weight: SetTagPieceWeight
    set_tag_density: SetTagDensity
    import_tag_conversions: ImportTagConversions
    merge_ingredients: MergeIngredients
    split_alias: SplitAlias
    find_ingredient_lines: FindIngredientLines
    get_product_classification: GetProductClassification
    propose_product_ingredient: ProposeProductIngredient
    confirm_product_ingredient: ConfirmProductIngredient
    reject_product_ingredient: RejectProductIngredient
    delete_product_ingredient: DeleteProductIngredient
    delete_rejected_product_ingredients: DeleteRejectedProductIngredients
    import_ingredient_names: ImportIngredientNames
    accept_candidate_as_ingredient: AcceptCandidateAsIngredient
    accept_candidate_as_alias: AcceptCandidateAsAlias
    dismiss_candidate: DismissCandidate
    ollama_settings: OllamaSettings
    memberships: HouseholdMembershipReader
    transactions: TransactionManager

    @contextmanager
    def open_product_analysis(self) -> Iterator[AnalyzeProductIngredient]:
        with open_ollama_chat(self.ollama_settings) as chat:
            yield AnalyzeProductIngredient(
                DjangoProductRepository(),
                DjangoIngredientRepository(),
                DjangoProductClassificationRepository(),
                OllamaIngredientClassifier(chat),
                self.memberships,
                self.transactions,
            )

    @contextmanager
    def open_line_interpretation(self) -> Iterator[InterpretIngredientLines]:
        with open_ollama_chat(self.ollama_settings) as chat:
            yield InterpretIngredientLines(
                DjangoIngredientLineRepository(),
                OllamaIngredientLineInterpreter(chat),
                self.list_tags,
            )

    @contextmanager
    def open_candidate_curation(self, batch_size: int) -> Iterator[CurateCandidates]:
        with open_ollama_chat(self.ollama_settings) as chat:
            yield CurateCandidates(
                DjangoCandidateRepository(),
                self.list_tags,
                OllamaCandidateCurator(chat),
                self.accept_candidate_as_ingredient,
                self.accept_candidate_as_alias,
                self.dismiss_candidate,
                batch_size,
            )

    @contextmanager
    def open_tag_unification(self) -> Iterator[UnifyTags]:
        with open_ollama_chat(self.ollama_settings) as chat:
            yield UnifyTags(self.list_tags, OllamaTagUnifier(chat), self.merge_ingredients)

    @contextmanager
    def open_classification(self, question_limit: int) -> Iterator[ProposeIngredientsForProducts]:
        with open_ollama_chat(self.ollama_settings) as chat:
            yield ProposeIngredientsForProducts(
                DjangoProductRepository(),
                DjangoIngredientRepository(),
                DjangoProductClassificationRepository(),
                OllamaIngredientClassifier(chat),
                self.transactions,
                question_limit,
            )


def build_catalog(
    memberships: HouseholdMembershipReader,
    references: tuple[IngredientReferences, ...],
    ollama_settings: OllamaSettings,
    transactions: TransactionManager,
) -> CatalogModule:
    lines = DjangoIngredientLineRepository()
    products = DjangoProductRepository()
    ingredients = DjangoIngredientRepository()
    classifications = DjangoProductClassificationRepository()
    candidates = DjangoCandidateRepository()
    describe_products = DescribeHouseholdProducts(products, classifications, ingredients)
    return CatalogModule(
        list_household_products=ListHouseholdProducts(products, memberships),
        create_product=CreateProduct(products, memberships, transactions),
        update_product=UpdateProduct(products, memberships, transactions),
        delete_product=DeleteProduct(products, memberships),
        find_household_product=FindHouseholdProduct(products),
        describe_household_products=describe_products,
        get_product_nutrition=GetProductNutrition(describe_products, ingredients),
        list_measurement_units=ListMeasurementUnits(),
        create_ingredient=CreateIngredient(ingredients, transactions),
        add_ingredient_alias=AddIngredientAlias(ingredients, transactions),
        find_ingredient_by_name=FindIngredientByName(ingredients),
        find_ingredients_by_names=FindIngredientsByNames(ingredients),
        get_ingredients=GetIngredients(ingredients),
        search_ingredients=SearchIngredients(ingredients),
        list_tags=ListTags(ingredients),
        set_tag_calories=SetTagCalories(ingredients, transactions),
        import_tag_calories=ImportTagCalories(ingredients, transactions),
        set_tag_piece_weight=SetTagPieceWeight(ingredients, transactions),
        set_tag_density=SetTagDensity(ingredients, transactions),
        import_tag_conversions=ImportTagConversions(ingredients, transactions),
        merge_ingredients=MergeIngredients(
            ingredients, classifications, references, lines, transactions
        ),
        find_ingredient_lines=FindIngredientLines(lines),
        split_alias=SplitAlias(ingredients, transactions),
        get_product_classification=GetProductClassification(
            classifications, ingredients, memberships
        ),
        propose_product_ingredient=ProposeProductIngredient(
            classifications, ingredients, transactions
        ),
        confirm_product_ingredient=ConfirmProductIngredient(
            classifications, ingredients, memberships, transactions
        ),
        reject_product_ingredient=RejectProductIngredient(
            classifications, memberships, transactions
        ),
        delete_product_ingredient=DeleteProductIngredient(
            classifications, memberships, transactions
        ),
        delete_rejected_product_ingredients=DeleteRejectedProductIngredients(
            classifications, memberships, transactions
        ),
        import_ingredient_names=ImportIngredientNames(ingredients, candidates, transactions),
        accept_candidate_as_ingredient=AcceptCandidateAsIngredient(
            candidates, ingredients, transactions
        ),
        accept_candidate_as_alias=AcceptCandidateAsAlias(candidates, ingredients, transactions),
        dismiss_candidate=DismissCandidate(candidates, ingredients, transactions),
        ollama_settings=ollama_settings,
        memberships=memberships,
        transactions=transactions,
    )
