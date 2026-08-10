from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0021_organization_showcase_sms_limits"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar_image",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
