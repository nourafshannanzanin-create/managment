from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0002_request_assigned_managers"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("two_factor_required", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "organization",
                    models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="preferences", to="workflow.organization"),
                ),
            ],
            options={
                "db_table": "organization_preferences",
            },
        ),
    ]
