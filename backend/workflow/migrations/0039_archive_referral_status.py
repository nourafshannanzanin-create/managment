from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0038_archive_documents"),
    ]

    operations = [
        migrations.AddField(
            model_name="archivereferral",
            name="status",
            field=models.CharField(
                choices=[("pending", "در حال بررسی"), ("approved", "تأیید شده")],
                db_index=True,
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="archivereferral",
            name="decided_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
