from django.db import migrations

DROP_PROVENANCE = """
ALTER TABLE recipes_recipe
    DROP CONSTRAINT IF EXISTS recipe_source_fields_complete,
    DROP CONSTRAINT IF EXISTS recipe_has_author_or_source;
ALTER TABLE recipes_recipe DROP INDEX IF EXISTS unique_recipe_source_reference;
ALTER TABLE recipes_recipe
    DROP COLUMN IF EXISTS source_image_url,
    DROP COLUMN IF EXISTS source_name,
    DROP COLUMN IF EXISTS source_recipe_id,
    DROP COLUMN IF EXISTS source_url,
    DROP COLUMN IF EXISTS yield_label;
ALTER TABLE recipes_recipe MODIFY created_by_id integer NOT NULL;
ALTER TABLE recipes_recipeingredient DROP COLUMN IF EXISTS source_text;
ALTER TABLE recipes_recipeingredient
    MODIFY name varchar(120) NOT NULL,
    MODIFY normalized_name varchar(120) NOT NULL,
    MODIFY quantity numeric(12, 3) NOT NULL;
"""


class Migration(migrations.Migration):
    dependencies = [("recipes", "0001_initial")]

    operations = [migrations.RunSQL(DROP_PROVENANCE, migrations.RunSQL.noop)]
