# Generated manually for showcase organizations and SMS limits

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0020_support_desk_platform_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="is_showcase",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="organizationpreference",
            name="sms_daily_limit",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="organizationpreference",
            name="sms_monthly_limit",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
