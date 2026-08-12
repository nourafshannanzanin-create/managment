from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0027_direct_message_attachment"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="password_plain",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
