import datetime

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0025_direct_conversation_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="organizationpreference",
            name="work_day_start_time",
            field=models.TimeField(default=datetime.time(9, 0)),
        ),
        migrations.AddField(
            model_name="organizationpreference",
            name="work_day_end_time",
            field=models.TimeField(default=datetime.time(17, 0)),
        ),
        migrations.AddField(
            model_name="organizationpreference",
            name="monthly_leave_hours",
            field=models.PositiveIntegerField(default=20),
        ),
        migrations.AddField(
            model_name="request",
            name="request_type",
            field=models.CharField(
                choices=[
                    ("general", "عمومی"),
                    ("leave_hourly", "مرخصی ساعتی"),
                    ("leave_daily", "مرخصی روزانه"),
                    ("mission", "مأموریت"),
                    ("overtime", "اضافه‌کار"),
                    ("remote", "دورکاری"),
                    ("purchase", "خرید/تدارکات"),
                ],
                db_index=True,
                default="general",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="LeaveRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "mode",
                    models.CharField(
                        choices=[("hourly", "ساعتی"), ("daily", "روزانه")],
                        default="hourly",
                        max_length=16,
                    ),
                ),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("hours", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "پیش نویس"),
                            ("submitted", "ثبت شده"),
                            ("under_review", "در بررسی"),
                            ("approved", "تایید شده"),
                            ("rejected", "رد شده"),
                            ("closed", "بسته شده"),
                        ],
                        default="submitted",
                        max_length=32,
                    ),
                ),
                (
                    "request",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="leave_request",
                        to="workflow.request",
                    ),
                ),
            ],
            options={
                "db_table": "leave_requests",
            },
        ),
        migrations.AddIndex(
            model_name="leaverequest",
            index=models.Index(fields=["starts_at", "ends_at"], name="idx_leave_request_range"),
        ),
    ]
