from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0003_organizationpreference"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectionAccessGrant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("section_key", models.CharField(db_index=True, max_length=40)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="section_access_grants", to="workflow.organization")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="section_access_grants", to="workflow.user")),
            ],
            options={
                "db_table": "section_access_grants",
            },
        ),
        migrations.AddConstraint(
            model_name="sectionaccessgrant",
            constraint=models.UniqueConstraint(fields=("organization", "section_key", "user"), name="uq_section_access_grant"),
        ),
    ]
