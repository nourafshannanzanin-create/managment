from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0029_tasking_module"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserEntrustedItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("title", models.CharField(max_length=180)),
                ("amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("entrusted_at", models.DateField(default=django.utils.timezone.localdate)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entrusted_items",
                        to="workflow.user",
                    ),
                ),
            ],
            options={
                "db_table": "user_entrusted_items",
                "ordering": ["-entrusted_at", "-id"],
            },
        ),
    ]
