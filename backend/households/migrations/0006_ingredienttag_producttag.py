from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("households", "0005_seed_product_name_aliases")]
    operations = [
        migrations.CreateModel(
            name="IngredientTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("normalized_name", models.CharField(max_length=120, unique=True)),
                ("source", models.CharField(default="ania_gotuje", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="ProductTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(default="manual", max_length=32)),
                ("is_verified", models.BooleanField(default=False)),
                ("ingredient_tag", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="product_tags", to="households.ingredienttag")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="product_tags", to="households.product")),
            ],
            options={"ordering": ["ingredient_tag__name"], "constraints": [models.UniqueConstraint(fields=("product", "ingredient_tag"), name="unique_product_ingredient_tag")]},
        ),
    ]
