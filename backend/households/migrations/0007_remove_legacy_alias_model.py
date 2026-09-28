import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("households", "0006_ingredienttag_producttag")]

    operations = [
        migrations.DeleteModel(name="ProductAlias"),
        migrations.RenameModel(old_name="IngredientAliasProposal", new_name="TagProposal"),
        migrations.RenameIndex(
            model_name="tagproposal",
            old_name="households__househo_c11ac6_idx",
            new_name="households__househo_926d8e_idx",
        ),
        migrations.AddField(
            model_name="product",
            name="ingredient_tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="products",
                through="households.ProductTag",
                to="households.ingredienttag",
            ),
        ),
        migrations.AlterField(
            model_name="tagproposal",
            name="household",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tag_proposals",
                to="households.household",
            ),
        ),
        migrations.AlterField(
            model_name="tagproposal",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tag_proposals",
                to="households.product",
            ),
        ),
    ]
