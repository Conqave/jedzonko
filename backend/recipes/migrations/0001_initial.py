import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RecipeCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=80, unique=True)),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("name", ""), _negated=True),
                        name="recipe_category_name_not_empty",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Recipe",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("servings", models.PositiveSmallIntegerField()),
                ("preparation_time_minutes", models.PositiveSmallIntegerField()),
                ("cooking_time_minutes", models.PositiveSmallIntegerField()),
                (
                    "difficulty",
                    models.CharField(
                        choices=[("easy", "easy"), ("medium", "medium"), ("hard", "hard")],
                        max_length=16,
                    ),
                ),
                ("image", models.ImageField(blank=True, null=True, upload_to="recipes/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DB_SET_NULL,
                        related_name="created_recipes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DB_SET_NULL,
                        related_name="recipes",
                        to="recipes.recipecategory",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="RecipeTag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=60, unique=True)),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("name", ""), _negated=True),
                        name="recipe_tag_name_not_empty",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="RecipeTagging",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE, to="recipes.recipe"
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE, to="recipes.recipetag"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="recipe",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="recipes",
                through="recipes.RecipeTagging",
                to="recipes.recipetag",
            ),
        ),
        migrations.CreateModel(
            name="RecipeIngredient",
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
                    "ingredient",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="recipe_lines",
                        to="catalog.ingredient",
                    ),
                ),
                (
                    "recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="ingredients",
                        to="recipes.recipe",
                    ),
                ),
            ],
            options={
                "ordering": ["recipe_id", "name"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("recipe", "normalized_name"), name="unique_recipe_ingredient"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("name", ""), _negated=True),
                        name="recipe_ingredient_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("normalized_name", ""), _negated=True),
                        name="recipe_ingredient_normalized_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("unit_code__in", ("g", "kg", "ml", "l", "szt", "opak"))
                        ),
                        name="recipe_ingredient_unit_known",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("quantity__gt", 0)),
                        name="recipe_ingredient_quantity_positive",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="RecipeStep",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("position", models.PositiveSmallIntegerField()),
                ("text", models.TextField()),
                (
                    "recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="steps",
                        to="recipes.recipe",
                    ),
                ),
            ],
            options={
                "ordering": ["recipe_id", "position"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("recipe", "position"), name="unique_recipe_step_position"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("position__gte", 1)),
                        name="recipe_step_position_from_one",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("text", ""), _negated=True),
                        name="recipe_step_text_not_empty",
                    ),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="recipetagging",
            constraint=models.UniqueConstraint(
                fields=("recipe", "tag"), name="unique_recipe_tagging"
            ),
        ),
        migrations.AddIndex(
            model_name="recipe",
            index=models.Index(fields=["name"], name="recipes_rec_name_891f25_idx"),
        ),
        migrations.AddConstraint(
            model_name="recipe",
            constraint=models.CheckConstraint(
                condition=models.Q(("name", ""), _negated=True), name="recipe_name_not_empty"
            ),
        ),
        migrations.AddConstraint(
            model_name="recipe",
            constraint=models.CheckConstraint(
                condition=models.Q(("servings__gte", 1)), name="recipe_serves_someone"
            ),
        ),
        migrations.AddConstraint(
            model_name="recipe",
            constraint=models.CheckConstraint(
                condition=models.Q(("difficulty__in", ["easy", "medium", "hard"])),
                name="recipe_difficulty_known",
            ),
        ),
    ]
