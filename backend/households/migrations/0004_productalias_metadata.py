from django.db import migrations, models


def mark_existing_aliases_verified(apps, schema_editor):
    ProductAlias = apps.get_model("households", "ProductAlias")
    ProductAlias.objects.update(is_verified=True)


class Migration(migrations.Migration):
    dependencies = [("households", "0003_ingredientaliasproposal")]

    operations = [
        migrations.AddField(
            model_name="productalias",
            name="source",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("ania_gotuje", "Ania Gotuje"),
                    ("ollama", "Ollama"),
                    ("admin", "Admin"),
                ],
                default="manual",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="productalias",
            name="is_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(mark_existing_aliases_verified, migrations.RunPython.noop),
    ]
