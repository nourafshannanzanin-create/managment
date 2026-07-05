from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0004_sectionaccessgrant"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="assigned_employees",
            field=models.ManyToManyField(blank=True, related_name="employee_assigned_requests", to="workflow.user"),
        ),
    ]
