import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
        ("households", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=80)),
                (
                    "household",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="inventory_categories",
                        to="households.household",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="InventoryItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "unit_code",
                    models.CharField(
                        choices=[
                            ("g", "gram"),
                            ("kg", "kilogram"),
                            ("ml", "mililitr"),
                            ("l", "litr"),
                            ("szt", "sztuka"),
                            ("opak", "opakowanie"),
                        ],
                        max_length=16,
                    ),
                ),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=12)),
                (
                    "minimum_quantity",
                    models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True),
                ),
                ("photo", models.ImageField(blank=True, null=True, upload_to="inventory/")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DB_SET_NULL,
                        related_name="inventory_items",
                        to="inventory.inventorycategory",
                    ),
                ),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="inventory_item",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "ordering": ["product__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="inventorycategory",
            constraint=models.UniqueConstraint(
                fields=("household", "name"), name="unique_inventory_category_per_household"
            ),
        ),
        migrations.AddConstraint(
            model_name="inventorycategory",
            constraint=models.CheckConstraint(
                condition=models.Q(("name", ""), _negated=True),
                name="inventory_category_name_not_empty",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("unit_code__in", ("g", "kg", "ml", "l", "szt", "opak"))),
                name="inventory_item_unit_known",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gte", 0)),
                name="inventory_item_quantity_not_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("minimum_quantity__isnull", True),
                    ("minimum_quantity__gte", 0),
                    _connector="OR",
                ),
                name="inventory_item_minimum_not_negative",
            ),
        ),
    ]
