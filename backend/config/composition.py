from dataclasses import dataclass
from functools import cache

from django.conf import settings

from accounts.composition import AccountsModule, build_accounts
from accounts.infrastructure.promotions_access import PromotionsAccess
from catalog.composition import CatalogModule, build_catalog
from catalog.infrastructure.feature_ingredient_references import (
    RecipeIngredientReferences,
    ShoppingIngredientReferences,
)
from config.transactions import DjangoTransactionManager
from households.composition import HouseholdsModule, build_households, build_membership_reader
from households.infrastructure.shopping_household_provisioner import ShoppingHouseholdProvisioner
from inventory.composition import InventoryModule, build_inventory
from inventory.infrastructure.catalog_products import (
    CatalogProductDirectory,
)
from promotions.composition import PromotionsModule, PromotionSourceSettings, build_promotions
from recipes.composition import (
    RecipesModule,
    RecipeSourceSettings,
    build_reassign_recipe_ingredient,
    build_recipes,
)
from recipes.infrastructure.catalog_ingredient_lines import CatalogIngredientLines
from recipes.infrastructure.catalog_ingredient_resolver import CatalogIngredientResolver
from recipes.infrastructure.inventory_consumer import InventoryConsumer
from recipes.infrastructure.pantry_stock_reader import PantryStockReader
from shared.infrastructure.ollama_chat import OllamaSettings
from shopping.composition import (
    ShoppingModule,
    build_create_primary_shopping_list,
    build_reassign_shopping_ingredient,
    build_shopping,
)
from shopping.infrastructure.catalog_directory import CatalogDirectory
from shopping.infrastructure.catalog_line_interpreter import CatalogLineInterpreter
from shopping.infrastructure.catalog_tagged_product_creator import CatalogTaggedProductCreator
from shopping.infrastructure.inventory_stock_gateway import InventoryStockGateway
from shopping.infrastructure.inventory_writer_gateway import InventoryWriterGateway
from shopping.infrastructure.promotions_coverage_reader import PromotionsCoverageReader
from shopping.infrastructure.recipe_requirement_gateway import RecipeRequirementGateway


@dataclass(frozen=True, slots=True)
class Container:
    accounts: AccountsModule
    households: HouseholdsModule
    catalog: CatalogModule
    inventory: InventoryModule
    recipes: RecipesModule
    shopping: ShoppingModule
    promotions: PromotionsModule


@cache
def container() -> Container:
    memberships = build_membership_reader()
    transactions = DjangoTransactionManager()

    create_primary_list = build_create_primary_shopping_list()
    provisioner = ShoppingHouseholdProvisioner(create_primary_list)
    households = build_households(provisioner, transactions)

    reassign_recipe_ingredient = build_reassign_recipe_ingredient()
    reassign_shopping_ingredient = build_reassign_shopping_ingredient()
    ingredient_references = (
        RecipeIngredientReferences(reassign_recipe_ingredient),
        ShoppingIngredientReferences(reassign_shopping_ingredient),
    )
    ollama_settings = OllamaSettings(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        think=settings.OLLAMA_REASONING_EFFORT,
        timeout_seconds=settings.OLLAMA_HTTP_TIMEOUT_SECONDS,
        max_output_tokens=settings.OLLAMA_MAX_OUTPUT_TOKENS,
        context_tokens=settings.OLLAMA_CONTEXT_TOKENS,
        max_context_tokens=settings.OLLAMA_MAX_CONTEXT_TOKENS,
    )
    catalog = build_catalog(memberships, ingredient_references, ollama_settings, transactions)

    product_directory = CatalogProductDirectory(catalog.find_household_product)
    inventory = build_inventory(memberships, product_directory, transactions)

    stock = PantryStockReader(
        inventory.get_household_inventory, catalog.describe_household_products
    )
    resolver = CatalogIngredientResolver(catalog.find_ingredients_by_names)
    recipe_lines = CatalogIngredientLines(
        catalog.find_ingredient_lines, catalog.open_line_interpretation
    )
    consumer = InventoryConsumer(inventory.consume_inventory_quantity)
    recipe_source_settings = RecipeSourceSettings(
        timeout_seconds=settings.RECIPE_SOURCE_HTTP_TIMEOUT_SECONDS,
        user_agent=settings.RECIPE_SOURCE_HTTP_USER_AGENT,
        suggestion_ingredient_limit=settings.RECIPE_SOURCE_SUGGESTION_INGREDIENT_LIMIT,
    )
    recipes = build_recipes(
        memberships,
        stock,
        resolver,
        recipe_lines,
        consumer,
        reassign_recipe_ingredient,
        recipe_source_settings,
        transactions,
    )

    promotion_source_settings = PromotionSourceSettings(
        timeout_seconds=settings.PROMOTIONS_HTTP_TIMEOUT_SECONDS,
        user_agent=settings.PROMOTIONS_HTTP_USER_AGENT,
        search_leaflet_limit=settings.PROMOTIONS_SEARCH_LEAFLET_LIMIT,
        search_result_limit=settings.PROMOTIONS_SEARCH_RESULT_LIMIT,
    )
    promotions = build_promotions(promotion_source_settings)

    catalog_directory = CatalogDirectory(
        catalog.find_household_product, catalog.get_ingredients, catalog.describe_household_products
    )
    stock_levels = InventoryStockGateway(inventory.get_household_inventory)
    inventory_writer = InventoryWriterGateway(inventory.add_quantity_to_inventory)
    tagged_products = CatalogTaggedProductCreator(
        catalog.create_product, catalog.confirm_product_ingredient
    )
    recipe_requirements = RecipeRequirementGateway(
        recipes.calculate_missing_recipe_items, recipes.open_external
    )
    promotion_coverage = PromotionsCoverageReader(
        promotions.open_source, promotions.check_promotion_access
    )
    shopping = build_shopping(
        memberships,
        catalog_directory,
        stock_levels,
        inventory_writer,
        tagged_products,
        recipe_requirements,
        promotion_coverage,
        CatalogLineInterpreter(catalog.open_line_interpretation),
        transactions,
    )

    promotion_access = PromotionsAccess(promotions.check_promotion_access)
    accounts = build_accounts(promotion_access)

    return Container(
        accounts=accounts,
        households=households,
        catalog=catalog,
        inventory=inventory,
        recipes=recipes,
        shopping=shopping,
        promotions=promotions,
    )
