from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0036_live_outbox"),
    ]

    operations = [
        migrations.CreateModel(
            name="IdempotencyRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=128)),
                ("method", models.CharField(max_length=10)),
                ("path", models.CharField(max_length=255)),
                ("request_hash", models.CharField(max_length=64)),
                ("status_code", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("response_body", models.TextField(blank=True, default="")),
                ("content_type", models.CharField(blank=True, default="application/json", max_length=120)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="idempotency_records", to="workflow.user")),
            ],
            options={"db_table": "idempotency_records"},
        ),
        migrations.AddConstraint(
            model_name="idempotencyrecord",
            constraint=models.UniqueConstraint(fields=("user", "key", "method", "path"), name="uq_idempotency_user_key_route"),
        ),
        migrations.AddIndex(
            model_name="idempotencyrecord",
            index=models.Index(fields=["created_at"], name="idx_idempotency_created"),
        ),
    ]
