from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0014_user_bonus_penalty"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="finance_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
