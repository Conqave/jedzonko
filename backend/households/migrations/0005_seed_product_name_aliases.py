from django.db import migrations


def seed_product_name_aliases(apps, schema_editor):
    Product = apps.get_model("households", "Product")
    ProductAlias = apps.get_model("households", "ProductAlias")
    for product in Product.objects.all().iterator():
        ProductAlias.objects.get_or_create(
            product_id=product.id,
            normalized_name=product.normalized_name,
            defaults={
                "name": product.name,
                "source": "manual",
                "is_verified": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("households", "0004_productalias_metadata")]
    operations = [migrations.RunPython(seed_product_name_aliases, migrations.RunPython.noop)]
