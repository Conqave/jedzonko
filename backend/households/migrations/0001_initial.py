import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Household",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("name", ""), _negated=True),
                        name="household_name_not_empty",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="HouseholdMembership",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                (
                    "household",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="memberships",
                        to="households.household",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DB_CASCADE,
                        related_name="household_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["household_id", "user_id"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("household", "user"), name="unique_household_member"
                    )
                ],
            },
        ),
    ]
