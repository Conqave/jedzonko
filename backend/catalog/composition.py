from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from catalog.application.ports.ingredient_references import IngredientReferences
from catalog.application.use_cases.add_ingredient_alias import AddIngredientAlias
from catalog.application.use_cases.analyze_product_ingredient import AnalyzeProductIngredient
from catalog.application.use_cases.confirm_product_ingredient import ConfirmProductIngredient
from catalog.application.use_cases.create_ingredient import CreateIngredient
from catalog.application.use_cases.create_product import CreateProduct
from catalog.application.use_cases.decide_candidate import (
    AcceptCandidateAsAlias,
    AcceptCandidateAsIngredient,
    DismissCandidate,
)
from catalog.application.use_cases.delete_product import DeleteProduct
from catalog.application.use_cases.describe_household_products import DescribeHouseholdProducts
from catalog.application.use_cases.find_household_product import FindHouseholdProduct
from catalog.application.use_cases.find_ingredient_by_name import FindIngredientByName
from catalog.application.use_cases.find_ingredients_by_names import FindIngredientsByNames
from catalog.application.use_cases.get_ingredients import GetIngredients
from catalog.application.use_cases.get_product_classification import GetProductClassification
from catalog.application.use_cases.import_ingredient_names import ImportIngredientNames
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
from catalog.application.use_cases.update_product import UpdateProduct
from catalog.infrastructure.django_candidate_repository import DjangoCandidateRepository
from catalog.infrastructure.django_ingredient_repository import DjangoIngredientRepository
from catalog.infrastructure.django_product_classification_repository import (
    DjangoProductClassificationRepository,
)
from catalog.infrastructure.django_product_repository import DjangoProductRepository
from catalog.infrastructure.providers.ollama.classifier import OllamaIngredientClassifier
from shared.household_membership import HouseholdMembershipReader
from shared.infrastructure.ollama_chat import OllamaSettings, open_ollama_chat
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class ClassifierSettings:
    ollama: OllamaSettings
    question_limit: int


@dataclass(frozen=True, slots=True)
class CatalogModule:
    list_household_products: ListHouseholdProducts
    create_product: CreateProduct
    update_product: UpdateProduct
    delete_product: DeleteProduct
    find_household_product: FindHouseholdProduct
    describe_household_products: DescribeHouseholdProducts
    list_measurement_units: ListMeasurementUnits
    create_ingredient: CreateIngredient
    add_ingredient_alias: AddIngredientAlias
    find_ingredient_by_name: FindIngredientByName
    find_ingredients_by_names: FindIngredientsByNames
    get_ingredients: GetIngredients
    search_ingredients: SearchIngredients
    list_tags: ListTags
    merge_ingredients: MergeIngredients
    get_product_classification: GetProductClassification
    propose_product_ingredient: ProposeProductIngredient
    confirm_product_ingredient: ConfirmProductIngredient
    reject_product_ingredient: RejectProductIngredient
    import_ingredient_names: ImportIngredientNames
    accept_candidate_as_ingredient: AcceptCandidateAsIngredient
    accept_candidate_as_alias: AcceptCandidateAsAlias
    dismiss_candidate: DismissCandidate
    classifier_settings: ClassifierSettings
    memberships: HouseholdMembershipReader
    transactions: TransactionManager

    @contextmanager
    def open_product_analysis(self) -> Iterator[AnalyzeProductIngredient]:
        with open_ollama_chat(self.classifier_settings.ollama) as chat:
            yield AnalyzeProductIngredient(
                DjangoProductRepository(),
                DjangoIngredientRepository(),
                DjangoProductClassificationRepository(),
                OllamaIngredientClassifier(chat),
                self.memberships,
                self.transactions,
            )

    @contextmanager
    def open_classification(self, question_limit: int) -> Iterator[ProposeIngredientsForProducts]:
        settings = self.classifier_settings
        with open_ollama_chat(settings.ollama) as chat:
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
    classifier_settings: ClassifierSettings,
    transactions: TransactionManager,
) -> CatalogModule:
    products = DjangoProductRepository()
    ingredients = DjangoIngredientRepository()
    classifications = DjangoProductClassificationRepository()
    candidates = DjangoCandidateRepository()
    return CatalogModule(
        list_household_products=ListHouseholdProducts(products, memberships),
        create_product=CreateProduct(products, memberships, transactions),
        update_product=UpdateProduct(products, memberships, transactions),
        delete_product=DeleteProduct(products, memberships),
        find_household_product=FindHouseholdProduct(products),
        describe_household_products=DescribeHouseholdProducts(
            products, classifications, ingredients
        ),
        list_measurement_units=ListMeasurementUnits(),
        create_ingredient=CreateIngredient(ingredients, transactions),
        add_ingredient_alias=AddIngredientAlias(ingredients, transactions),
        find_ingredient_by_name=FindIngredientByName(ingredients),
        find_ingredients_by_names=FindIngredientsByNames(ingredients),
        get_ingredients=GetIngredients(ingredients),
        search_ingredients=SearchIngredients(ingredients),
        list_tags=ListTags(ingredients),
        merge_ingredients=MergeIngredients(ingredients, classifications, references, transactions),
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
        import_ingredient_names=ImportIngredientNames(ingredients, candidates, transactions),
        accept_candidate_as_ingredient=AcceptCandidateAsIngredient(
            candidates, ingredients, transactions
        ),
        accept_candidate_as_alias=AcceptCandidateAsAlias(candidates, ingredients, transactions),
        dismiss_candidate=DismissCandidate(candidates, ingredients, transactions),
        classifier_settings=classifier_settings,
        memberships=memberships,
        transactions=transactions,
    )
