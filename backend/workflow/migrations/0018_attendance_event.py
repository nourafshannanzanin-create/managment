import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


def populate_attendance_tokens(apps, schema_editor):
    User = apps.get_model("workflow", "User")
    for user in User.objects.filter(attendance_token__isnull=True):
        user.attendance_token = uuid.uuid4().hex
        user.save(update_fields=["attendance_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0017_featurepurchase_subscription_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="attendance_token",
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True, unique=True),
        ),
        migrations.RunPython(populate_attendance_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="attendance_token",
            field=models.CharField(db_index=True, default=uuid.uuid4, max_length=64, unique=True),
        ),
        migrations.CreateModel(
            name="AttendanceEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("event_type", models.CharField(choices=[("in", "ورود"), ("out", "خروج")], max_length=12)),
                ("source", models.CharField(choices=[("manager", "ثبت مدیر"), ("link", "لینک پرسنل")], default="link", max_length=20)),
                ("note", models.TextField(blank=True)),
                ("event_at", models.DateTimeField(db_index=True, default=timezone.now)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_events", to="workflow.organization")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_events", to="workflow.user")),
            ],
            options={
                "db_table": "attendance_events",
            },
        ),
        migrations.AddIndex(
            model_name="attendanceevent",
            index=models.Index(fields=["organization", "-event_at"], name="idx_attendance_org_time"),
        ),
        migrations.AddIndex(
            model_name="attendanceevent",
            index=models.Index(fields=["user", "-event_at"], name="idx_attendance_user_time"),
        ),
    ]
