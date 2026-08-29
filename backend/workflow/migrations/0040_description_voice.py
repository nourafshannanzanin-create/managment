from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0039_archive_referral_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="description_voice",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="expense",
            name="description_voice",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="document",
            name="description_voice",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="task",
            name="description_voice",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="archivedocument",
            name="description_voice",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
