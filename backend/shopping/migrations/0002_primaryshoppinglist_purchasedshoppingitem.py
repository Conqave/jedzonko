from django.db import migrations

# The shopping schema is now created in full by 0001_initial. This migration is kept
# as an applied no-op so databases that already recorded it stay on the same chain.


class Migration(migrations.Migration):

    dependencies = [("shopping", "0001_initial")]

    operations: list[migrations.operations.base.Operation] = []
