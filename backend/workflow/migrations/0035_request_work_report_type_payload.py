from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0034_performance_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="type_payload",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
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
                    ("work_report", "گزارش کار"),
                ],
                db_index=True,
                default="general",
                max_length=32,
            ),
        ),
    ]
