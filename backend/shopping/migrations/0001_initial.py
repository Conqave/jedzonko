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
            name="ShoppingList",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "primary_household",
                    models.GeneratedField(
                        db_persist=True,
                        expression=models.Case(
                            models.When(is_primary=True, then=models.F("household")), default=None
                        ),
                        output_field=models.BigIntegerField(null=True),
                    ),
                ),
                (
                    "household",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="shopping_lists",
                        to="households.household",
                    ),
                ),
            ],
            options={
                "ordering": ["-is_primary", "name"],
            },
        ),
        migrations.CreateModel(
            name="ShoppingListItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("free_text", models.CharField(blank=True, max_length=120, null=True)),
                (
                    "unit_code",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("g", "gram"),
                            ("kg", "kilogram"),
                            ("ml", "mililitr"),
                            ("l", "litr"),
                            ("szt", "sztuka"),
                            ("opak", "opakowanie"),
                        ],
                        max_length=16,
                        null=True,
                    ),
                ),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=12)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "pending"), ("purchased", "purchased")], max_length=16
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("purchased_at", models.DateTimeField(blank=True, null=True)),
                (
                    "pending_product",
                    models.GeneratedField(
                        db_persist=True,
                        expression=models.Case(
                            models.When(status="pending", then=models.F("product")), default=None
                        ),
                        output_field=models.BigIntegerField(null=True),
                    ),
                ),
                (
                    "pending_ingredient",
                    models.GeneratedField(
                        db_persist=True,
                        expression=models.Case(
                            models.When(status="pending", then=models.F("ingredient")), default=None
                        ),
                        output_field=models.BigIntegerField(null=True),
                    ),
                ),
                (
                    "ingredient",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="shopping_list_items",
                        to="catalog.ingredient",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="shopping_list_items",
                        to="catalog.product",
                    ),
                ),
                (
                    "shopping_list",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="items",
                        to="shopping.shoppinglist",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="shoppinglist",
            constraint=models.UniqueConstraint(
                fields=("primary_household",), name="one_primary_shopping_list_per_household"
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglist",
            constraint=models.CheckConstraint(
                condition=models.Q(("name", ""), _negated=True), name="shopping_list_name_not_empty"
            ),
        ),
        migrations.AddIndex(
            model_name="shoppinglistitem",
            index=models.Index(fields=["shopping_list", "status"], name="shopping_item_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("free_text__isnull", True),
                        ("ingredient__isnull", True),
                        ("product__isnull", False),
                    ),
                    models.Q(
                        ("free_text__isnull", True),
                        ("ingredient__isnull", False),
                        ("product__isnull", True),
                    ),
                    models.Q(
                        ("free_text__isnull", False),
                        ("ingredient__isnull", True),
                        ("product__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="shopping_item_exactly_one_subject",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("free_text__isnull", True),
                    models.Q(("free_text", ""), _negated=True),
                    _connector="OR",
                ),
                name="shopping_item_free_text_not_empty",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("free_text__isnull", False), ("unit_code__isnull", False), _connector="OR"
                ),
                name="shopping_item_measured_subject_has_unit",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("unit_code__isnull", True),
                    ("unit_code__in", ("g", "kg", "ml", "l", "szt", "opak")),
                    _connector="OR",
                ),
                name="shopping_item_unit_known",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)), name="shopping_item_quantity_positive"
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["pending", "purchased"])),
                name="shopping_item_status_known",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("purchased_at__isnull", False), ("status", "purchased")),
                    models.Q(("purchased_at__isnull", True), ("status", "pending")),
                    _connector="OR",
                ),
                name="shopping_item_purchase_time",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.UniqueConstraint(
                fields=("shopping_list", "pending_product"), name="one_pending_item_per_product"
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppinglistitem",
            constraint=models.UniqueConstraint(
                fields=("shopping_list", "pending_ingredient"),
                name="one_pending_item_per_ingredient",
            ),
        ),
    ]
