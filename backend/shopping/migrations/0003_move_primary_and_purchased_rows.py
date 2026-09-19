from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def move_rows_to_new_tables(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    ShoppingList = apps.get_model("shopping", "ShoppingList")
    PrimaryShoppingList = apps.get_model("shopping", "PrimaryShoppingList")
    ShoppingListItem = apps.get_model("shopping", "ShoppingListItem")
    PurchasedShoppingItem = apps.get_model("shopping", "PurchasedShoppingItem")

    for shopping_list in ShoppingList.objects.filter(is_primary=True).order_by("pk"):
        if PrimaryShoppingList.objects.filter(household_id=shopping_list.household_id).exists():
            continue
        PrimaryShoppingList.objects.create(
            household_id=shopping_list.household_id, shopping_list=shopping_list
        )

    for item in ShoppingListItem.objects.filter(is_purchased=True).order_by("pk"):
        PurchasedShoppingItem.objects.create(
            shopping_list_id=item.shopping_list_id,
            ingredient_id=item.ingredient_id,
            free_text=item.free_text,
            unit_id=item.unit_id,
            quantity=item.quantity,
            created_at=item.created_at,
            purchased_at=item.purchased_at or item.created_at,
        )
        item.delete()


def move_rows_back(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    ShoppingList = apps.get_model("shopping", "ShoppingList")
    PrimaryShoppingList = apps.get_model("shopping", "PrimaryShoppingList")
    ShoppingListItem = apps.get_model("shopping", "ShoppingListItem")
    PurchasedShoppingItem = apps.get_model("shopping", "PurchasedShoppingItem")

    primary_ids = PrimaryShoppingList.objects.values_list("shopping_list_id", flat=True)
    ShoppingList.objects.filter(pk__in=list(primary_ids)).update(is_primary=True)
    PrimaryShoppingList.objects.all().delete()

    for purchased in PurchasedShoppingItem.objects.order_by("pk"):
        ShoppingListItem.objects.create(
            shopping_list_id=purchased.shopping_list_id,
            ingredient_id=purchased.ingredient_id,
            free_text=purchased.free_text,
            unit_id=purchased.unit_id,
            quantity=purchased.quantity,
            is_purchased=True,
            purchased_at=purchased.purchased_at,
        )
        purchased.delete()


class Migration(migrations.Migration):

    dependencies = [("shopping", "0002_primaryshoppinglist_purchasedshoppingitem")]

    operations = [migrations.RunPython(move_rows_to_new_tables, move_rows_back)]
