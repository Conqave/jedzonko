from decimal import Decimal

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

BASE_UNITS = [
    ("g", "gram", "mass", Decimal("1")),
    ("kg", "kilogram", "mass", Decimal("1000")),
    ("ml", "mililitr", "volume", Decimal("1")),
    ("l", "litr", "volume", Decimal("1000")),
    ("szt", "sztuka", "count", Decimal("1")),
    ("opak", "opakowanie", "count", Decimal("1")),
]


def create_base_units(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    measurement_unit = apps.get_model("catalog", "MeasurementUnit")
    for code, name, dimension, factor_to_base in BASE_UNITS:
        measurement_unit.objects.update_or_create(
            code=code,
            defaults={"name": name, "dimension": dimension, "factor_to_base": factor_to_base},
        )


def delete_base_units(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    measurement_unit = apps.get_model("catalog", "MeasurementUnit")
    measurement_unit.objects.filter(code__in=[code for code, _, _, _ in BASE_UNITS]).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [migrations.RunPython(create_base_units, delete_base_units)]
