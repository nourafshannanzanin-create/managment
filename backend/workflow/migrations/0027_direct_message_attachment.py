from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0026_work_hours_leave_request_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="directmessage",
            name="body",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="directmessage",
            name="attachment_original_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="directmessage",
            name="attachment_stored_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="directmessage",
            name="attachment_mime_type",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="directmessage",
            name="attachment_size_bytes",
            field=models.IntegerField(default=0),
        ),
    ]
