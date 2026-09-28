from dataclasses import dataclass
from functools import cache

from django.conf import settings

from accounts.composition import AccountsModule, build_accounts
from accounts.infrastructure.promotions_access import PromotionsAccess
from catalog.composition import CatalogModule, ClassifierSettings, build_catalog
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
    CatalogProductRenamer,
)
from promotions.composition import PromotionsModule, PromotionSourceSettings, build_promotions
from recipes.composition import (
    RecipesModule,
    RecipeSourceSettings,
    build_reassign_recipe_ingredient,
    build_recipes,
)
from recipes.infrastructure.catalog_ingredient_resolver import CatalogIngredientResolver
from recipes.infrastructure.inventory_consumer import InventoryConsumer
from recipes.infrastructure.pantry_stock_reader import PantryStockReader
from shopping.composition import (
    ShoppingModule,
    build_create_primary_shopping_list,
    build_reassign_shopping_ingredient,
    build_shopping,
)
from shopping.infrastructure.catalog_directory import CatalogDirectory
from shopping.infrastructure.inventory_stock_gateway import InventoryStockGateway
from shopping.infrastructure.inventory_writer_gateway import InventoryWriterGateway
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
    classifier_settings = ClassifierSettings(
        base_url=settings.INGREDIENT_CLASSIFIER_BASE_URL,
        model=settings.INGREDIENT_CLASSIFIER_MODEL,
        think=settings.INGREDIENT_CLASSIFIER_REASONING_EFFORT,
        timeout_seconds=settings.INGREDIENT_CLASSIFIER_HTTP_TIMEOUT_SECONDS,
        question_limit=settings.INGREDIENT_CLASSIFIER_QUESTION_LIMIT,
    )
    catalog = build_catalog(memberships, ingredient_references, classifier_settings, transactions)

    product_directory = CatalogProductDirectory(catalog.find_household_product)
    product_renamer = CatalogProductRenamer(catalog.rename_product)
    inventory = build_inventory(memberships, product_directory, product_renamer, transactions)

    stock = PantryStockReader(
        inventory.get_household_inventory, catalog.describe_household_products
    )
    resolver = CatalogIngredientResolver(catalog.find_ingredients_by_names)
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
        consumer,
        reassign_recipe_ingredient,
        recipe_source_settings,
        transactions,
    )

    catalog_directory = CatalogDirectory(
        catalog.find_household_product, catalog.get_ingredients, catalog.describe_household_products
    )
    stock_levels = InventoryStockGateway(inventory.get_household_inventory)
    inventory_writer = InventoryWriterGateway(inventory.add_quantity_to_inventory)
    recipe_requirements = RecipeRequirementGateway(recipes.calculate_missing_recipe_items)
    shopping = build_shopping(
        memberships,
        catalog_directory,
        stock_levels,
        inventory_writer,
        recipe_requirements,
        transactions,
    )

    promotion_source_settings = PromotionSourceSettings(
        timeout_seconds=settings.PROMOTIONS_HTTP_TIMEOUT_SECONDS,
        user_agent=settings.PROMOTIONS_HTTP_USER_AGENT,
        search_leaflet_limit=settings.PROMOTIONS_SEARCH_LEAFLET_LIMIT,
        search_result_limit=settings.PROMOTIONS_SEARCH_RESULT_LIMIT,
    )
    promotions = build_promotions(promotion_source_settings)
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
