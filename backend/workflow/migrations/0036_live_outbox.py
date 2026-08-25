from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0035_request_work_report_type_payload"),
    ]

    operations = [
        migrations.CreateModel(
            name="LiveOutbox",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tenant_id", models.BigIntegerField(blank=True, null=True)),
                ("event_type", models.CharField(max_length=80)),
                ("entity_type", models.CharField(max_length=40)),
                ("entity_id", models.CharField(max_length=100)),
                ("action", models.CharField(default="updated", max_length=24)),
                ("actor_user_id", models.BigIntegerField(blank=True, null=True)),
                ("version", models.CharField(blank=True, default="", max_length=64)),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={"db_table": "live_outbox"},
        ),
        migrations.AddIndex(
            model_name="liveoutbox",
            index=models.Index(fields=["tenant_id", "id"], name="idx_live_outbox_tenant_id"),
        ),
    ]
