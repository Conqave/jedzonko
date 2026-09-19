import pytest
from django.apps import apps
from django.db import connection
from django.db.models import UniqueConstraint

pytestmark = pytest.mark.django_db


def _declared_constraints() -> list[tuple[str, str, object]]:
    declared: list[tuple[str, str, object]] = []
    for model in apps.get_models():
        for constraint in model._meta.constraints:
            declared.append((model._meta.db_table, constraint.name, constraint))
    return declared


def test_every_declared_constraint_exists_in_the_database() -> None:
    missing: list[str] = []
    with connection.cursor() as cursor:
        for table, name, _ in _declared_constraints():
            present = connection.introspection.get_constraints(cursor, table)
            if name not in present:
                missing.append(f"{table}.{name}")

    assert missing == []


def test_no_unique_constraint_relies_on_an_unsupported_partial_index() -> None:
    if connection.features.supports_partial_indexes:
        pytest.skip(
            "The database enforces partial indexes, so conditions are not silently dropped."
        )

    conditional = [
        f"{table}.{name}"
        for table, name, constraint in _declared_constraints()
        if isinstance(constraint, UniqueConstraint) and constraint.condition is not None
    ]

    assert conditional == []
