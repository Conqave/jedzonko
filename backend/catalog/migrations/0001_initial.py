from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("households", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ingredient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                (
                    "kcal_per_100g",
                    models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True),
                ),
                (
                    "kcal_source",
                    models.CharField(
                        blank=True,
                        choices=[("manual", "manual"), ("reference", "reference")],
                        max_length=16,
                        null=True,
                    ),
                ),
                ("kcal_reference_url", models.URLField(blank=True, max_length=500, null=True)),
                (
                    "grams_per_piece",
                    models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True),
                ),
                (
                    "piece_weight_source",
                    models.CharField(
                        blank=True,
                        choices=[("manual", "manual"), ("reference", "reference")],
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "piece_weight_reference_url",
                    models.URLField(blank=True, max_length=500, null=True),
                ),
                (
                    "grams_per_ml",
                    models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True),
                ),
                (
                    "density_source",
                    models.CharField(
                        blank=True,
                        choices=[("manual", "manual"), ("reference", "reference")],
                        max_length=16,
                        null=True,
                    ),
                ),
                ("density_reference_url", models.URLField(blank=True, max_length=500, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("name", ""), _negated=True),
                        name="ingredient_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("kcal_per_100g__isnull", True),
                            models.Q(
                                ("kcal_per_100g__gte", 0), ("kcal_per_100g__lte", Decimal("900"))
                            ),
                            _connector="OR",
                        ),
                        name="ingredient_kcal_in_range",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("kcal_per_100g__isnull", True),
                                ("kcal_reference_url__isnull", True),
                                ("kcal_source__isnull", True),
                            ),
                            models.Q(
                                ("kcal_per_100g__isnull", False),
                                ("kcal_reference_url__isnull", True),
                                ("kcal_source", "manual"),
                                ("kcal_source__isnull", False),
                            ),
                            models.Q(
                                ("kcal_per_100g__isnull", False),
                                ("kcal_reference_url__isnull", False),
                                ("kcal_source", "reference"),
                                ("kcal_source__isnull", False),
                                models.Q(("kcal_reference_url", ""), _negated=True),
                            ),
                            _connector="OR",
                        ),
                        name="ingredient_kcal_provenance",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("grams_per_piece__isnull", True),
                            models.Q(
                                ("grams_per_piece__gt", 0),
                                ("grams_per_piece__lte", Decimal("10000")),
                            ),
                            _connector="OR",
                        ),
                        name="ingredient_piece_weight_in_range",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("grams_per_piece__isnull", True),
                                ("piece_weight_reference_url__isnull", True),
                                ("piece_weight_source__isnull", True),
                            ),
                            models.Q(
                                ("grams_per_piece__isnull", False),
                                ("piece_weight_reference_url__isnull", True),
                                ("piece_weight_source", "manual"),
                                ("piece_weight_source__isnull", False),
                            ),
                            models.Q(
                                ("grams_per_piece__isnull", False),
                                ("piece_weight_reference_url__isnull", False),
                                ("piece_weight_source", "reference"),
                                ("piece_weight_source__isnull", False),
                                models.Q(("piece_weight_reference_url", ""), _negated=True),
                            ),
                            _connector="OR",
                        ),
                        name="ingredient_piece_weight_provenance",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("grams_per_ml__isnull", True),
                            models.Q(("grams_per_ml__gt", 0), ("grams_per_ml__lte", Decimal("3"))),
                            _connector="OR",
                        ),
                        name="ingredient_density_in_range",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("density_reference_url__isnull", True),
                                ("density_source__isnull", True),
                                ("grams_per_ml__isnull", True),
                            ),
                            models.Q(
                                ("density_reference_url__isnull", True),
                                ("density_source", "manual"),
                                ("density_source__isnull", False),
                                ("grams_per_ml__isnull", False),
                            ),
                            models.Q(
                                ("density_reference_url__isnull", False),
                                ("density_source", "reference"),
                                ("density_source__isnull", False),
                                ("grams_per_ml__isnull", False),
                                models.Q(("density_reference_url", ""), _negated=True),
                            ),
                            _connector="OR",
                        ),
                        name="ingredient_density_provenance",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="IngredientNameCandidate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("normalized_name", models.CharField(max_length=120, unique=True)),
                (
                    "source",
                    models.CharField(
                        choices=[("manual", "manual"), ("ania_gotuje", "ania_gotuje")],
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "pending"),
                            ("accepted", "accepted"),
                            ("dismissed", "dismissed"),
                        ],
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["status", "name"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("name", ""), _negated=True),
                        name="candidate_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("normalized_name", ""), _negated=True),
                        name="candidate_normalized_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("source__in", ["manual", "ania_gotuje"])),
                        name="candidate_source_known",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ["pending", "accepted", "dismissed"])),
                        name="candidate_status_known",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("decided_at__isnull", True), ("status", "pending")),
                            models.Q(
                                models.Q(("status", "pending"), _negated=True),
                                ("decided_at__isnull", False),
                            ),
                            _connector="OR",
                        ),
                        name="candidate_decision_time",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("normalized_name", models.CharField(max_length=120)),
                (
                    "default_unit_code",
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
                ("is_food", models.BooleanField(default=True)),
                (
                    "package_quantity",
                    models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True),
                ),
                (
                    "package_unit_code",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "household",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="products",
                        to="households.household",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="ProductIngredient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("proposed", "proposed"),
                            ("confirmed", "confirmed"),
                            ("rejected", "rejected"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[("manual", "manual"), ("model", "model")], max_length=16
                    ),
                ),
                ("model_name", models.CharField(blank=True, max_length=80, null=True)),
                ("proposed_at", models.DateTimeField(blank=True, null=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="product_links",
                        to="catalog.ingredient",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="ingredient_links",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "ordering": ["product_id", "ingredient_id"],
            },
        ),
        migrations.CreateModel(
            name="IngredientLine",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("normalized_text", models.CharField(max_length=255, unique=True)),
                (
                    "quantity",
                    models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True),
                ),
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
                ("model_name", models.CharField(max_length=120)),
                ("interpreted_at", models.DateTimeField()),
                (
                    "ingredient",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="lines",
                        to="catalog.ingredient",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("normalized_text", ""), _negated=True),
                        name="ingredient_line_text_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("model_name", ""), _negated=True),
                        name="ingredient_line_model_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("quantity__isnull", True), ("unit_code__isnull", True)),
                            models.Q(
                                ("quantity__gt", 0),
                                ("quantity__isnull", False),
                                ("unit_code__in", ("g", "kg", "ml", "l", "szt", "opak")),
                                ("unit_code__isnull", False),
                            ),
                            _connector="OR",
                        ),
                        name="ingredient_line_amount_complete",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="IngredientName",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("normalized_name", models.CharField(max_length=120, unique=True)),
                (
                    "kind",
                    models.CharField(
                        choices=[("canonical", "canonical"), ("alias", "alias")], max_length=16
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[("manual", "manual"), ("ania_gotuje", "ania_gotuje")],
                        max_length=16,
                    ),
                ),
                (
                    "canonical_ingredient",
                    models.GeneratedField(
                        db_persist=True,
                        expression=models.Case(
                            models.When(kind="canonical", then=models.F("ingredient")), default=None
                        ),
                        output_field=models.BigIntegerField(null=True),
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="names",
                        to="catalog.ingredient",
                    ),
                ),
            ],
            options={
                "ordering": ["ingredient_id", "kind", "name"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("canonical_ingredient",), name="one_canonical_name_per_ingredient"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("name", ""), _negated=True),
                        name="ingredient_name_text_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("normalized_name", ""), _negated=True),
                        name="ingredient_normalized_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("kind__in", ["canonical", "alias"])),
                        name="ingredient_name_kind_known",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("source__in", ["manual", "ania_gotuje"])),
                        name="ingredient_name_source_known",
                    ),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("household", "normalized_name"), name="unique_product_per_household"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(("name", ""), _negated=True), name="product_name_not_empty"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(("normalized_name", ""), _negated=True),
                name="product_normalized_name_not_empty",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("default_unit_code__in", ("g", "kg", "ml", "l", "szt", "opak"))
                ),
                name="product_default_unit_known",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("package_unit_code__isnull", True),
                    ("package_unit_code__in", ("g", "kg", "ml", "l", "szt", "opak")),
                    _connector="OR",
                ),
                name="product_package_unit_known",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("package_quantity__isnull", True), ("package_unit_code__isnull", True)
                    ),
                    models.Q(
                        ("package_quantity__isnull", False), ("package_unit_code__isnull", False)
                    ),
                    _connector="OR",
                ),
                name="product_package_quantity_requires_unit",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("package_quantity__isnull", True), ("package_quantity__gt", 0), _connector="OR"
                ),
                name="product_package_quantity_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="productingredient",
            constraint=models.UniqueConstraint(
                fields=("product", "ingredient"), name="one_link_per_product_ingredient"
            ),
        ),
        migrations.AddConstraint(
            model_name="productingredient",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["proposed", "confirmed", "rejected"])),
                name="product_ingredient_status_known",
            ),
        ),
        migrations.AddConstraint(
            model_name="productingredient",
            constraint=models.CheckConstraint(
                condition=models.Q(("source__in", ["manual", "model"])),
                name="product_ingredient_source_known",
            ),
        ),
        migrations.AddConstraint(
            model_name="productingredient",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("model_name__isnull", False),
                        ("proposed_at__isnull", False),
                        ("source", "model"),
                    ),
                    models.Q(
                        models.Q(("source", "model"), _negated=True), ("model_name__isnull", True)
                    ),
                    _connector="OR",
                ),
                name="product_ingredient_model_provenance",
            ),
        ),
        migrations.AddConstraint(
            model_name="productingredient",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("decided_at__isnull", True), ("status", "proposed")),
                    models.Q(
                        models.Q(("status", "proposed"), _negated=True),
                        ("decided_at__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="product_ingredient_decision_time",
            ),
        ),
    ]
