from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from shared.text import normalize_text

# Databases created before this release keyed inventory, shopping and recipe rows to the
# shared `catalog` dictionary tables, which 0001_initial no longer describes. Django cannot
# express that transition with state operations once the `catalog` app is gone, so the legacy
# tables are read, dropped and rebuilt here from the current model state. MariaDB cannot roll
# DDL back, so the migration runs outside a transaction and every step is guarded by the
# tables that are actually present. On a database built from zero it is a no-op.

LEGACY_TABLES = [
    "inventory_inventoryitem",
    "recipes_recipeingredient",
    "shopping_shoppinglistitem",
    "shopping_purchasedshoppingitem",
    "catalog_ingredient",
    "catalog_measurementunit",
]

REBUILT_MODELS = [
    ("households", "Product"),
    ("inventory", "InventoryItem"),
    ("recipes", "RecipeIngredient"),
    ("shopping", "ShoppingListItem"),
    ("shopping", "PurchasedShoppingItem"),
]


def convert_legacy_catalog_schema(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))

    unit_codes: dict[int, str] = {}
    ingredients: dict[int, tuple[str, str]] = {}
    list_households: dict[int, int] = {}
    inventory_rows: list[tuple[object, ...]] = []
    recipe_rows: list[tuple[object, ...]] = []
    pending_rows: list[tuple[object, ...]] = []
    purchased_rows: list[tuple[object, ...]] = []

    if "catalog_ingredient" in tables:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, code FROM catalog_measurementunit")
            unit_codes = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT id, name, default_unit_id FROM catalog_ingredient")
            ingredients = {row[0]: (row[1], unit_codes[row[2]]) for row in cursor.fetchall()}

            cursor.execute("SELECT id, household_id FROM shopping_shoppinglist")
            list_households = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute(
                "SELECT id, household_id, ingredient_id, unit_id, category_id, quantity,"
                " minimum_quantity, photo, updated_at FROM inventory_inventoryitem"
            )
            inventory_rows = list(cursor.fetchall())

            cursor.execute(
                "SELECT id, recipe_id, ingredient_id, unit_id, quantity"
                " FROM recipes_recipeingredient"
            )
            recipe_rows = list(cursor.fetchall())

            cursor.execute(
                "SELECT id, shopping_list_id, ingredient_id, free_text, unit_id, quantity,"
                " created_at FROM shopping_shoppinglistitem"
            )
            pending_rows = list(cursor.fetchall())

            cursor.execute(
                "SELECT id, shopping_list_id, ingredient_id, free_text, unit_id, quantity,"
                " created_at, purchased_at FROM shopping_purchasedshoppingitem"
            )
            purchased_rows = list(cursor.fetchall())

            for table in LEGACY_TABLES:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")

        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))

    for app_label, model_name in REBUILT_MODELS:
        model = apps.get_model(app_label, model_name)
        if model._meta.db_table not in tables:
            schema_editor.create_model(model)

    product_model = apps.get_model("households", "Product")
    owned_products: set[tuple[int, int]] = {(row[1], row[2]) for row in inventory_rows}
    for row in pending_rows + purchased_rows:
        if row[2] is not None:
            owned_products.add((list_households[row[1]], row[2]))

    products: dict[tuple[int, int], int] = {}
    for household_id, ingredient_id in sorted(owned_products):
        name, default_unit_code = ingredients[ingredient_id]
        product = product_model.objects.create(
            household_id=household_id,
            name=name,
            normalized_name=normalize_text(name),
            default_unit_code=default_unit_code,
            is_food=True,
        )
        products[(household_id, ingredient_id)] = product.pk

    inventory_item_model = apps.get_model("inventory", "InventoryItem")
    for row in inventory_rows:
        inventory_item_model.objects.create(
            id=row[0],
            household_id=row[1],
            product_id=products[(row[1], row[2])],
            unit_code=unit_codes[row[3]],
            category_id=row[4],
            quantity=row[5],
            minimum_quantity=row[6],
            photo=row[7] or "",
            updated_at=row[8],
        )

    recipe_ingredient_model = apps.get_model("recipes", "RecipeIngredient")
    for row in recipe_rows:
        name = ingredients[row[2]][0]
        recipe_ingredient_model.objects.create(
            id=row[0],
            recipe_id=row[1],
            name=name,
            normalized_name=normalize_text(name),
            unit_code=unit_codes[row[3]],
            quantity=row[4],
        )

    shopping_item_model = apps.get_model("shopping", "ShoppingListItem")
    for row in pending_rows:
        household_id = list_households[row[1]]
        shopping_item_model.objects.create(
            id=row[0],
            shopping_list_id=row[1],
            product_id=None if row[2] is None else products[(household_id, row[2])],
            free_text=row[3],
            unit_code=None if row[4] is None else unit_codes[row[4]],
            quantity=row[5],
            created_at=row[6],
        )

    purchased_item_model = apps.get_model("shopping", "PurchasedShoppingItem")
    for row in purchased_rows:
        household_id = list_households[row[1]]
        purchased_item_model.objects.create(
            id=row[0],
            shopping_list_id=row[1],
            product_id=None if row[2] is None else products[(household_id, row[2])],
            free_text=row[3],
            unit_code=None if row[4] is None else unit_codes[row[4]],
            quantity=row[5],
            created_at=row[6],
            purchased_at=row[7],
        )

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM django_migrations WHERE app = 'catalog'")
        cursor.execute(
            "DELETE FROM auth_permission WHERE content_type_id IN"
            " (SELECT id FROM django_content_type WHERE app_label = 'catalog')"
        )
        cursor.execute("DELETE FROM django_content_type WHERE app_label = 'catalog'")


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("households", "0001_initial"),
        ("inventory", "0001_initial"),
        ("recipes", "0001_initial"),
        ("shopping", "0004_alter_shoppinglist_options_and_more"),
    ]

    operations = [migrations.RunPython(convert_legacy_catalog_schema)]
