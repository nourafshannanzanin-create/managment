from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="assigned_managers",
            field=models.ManyToManyField(blank=True, related_name="assigned_requests", to="workflow.user"),
        ),
    ]
