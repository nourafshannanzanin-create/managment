from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0013_merge_20260713_0910"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="bonus_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18),
        ),
        migrations.AddField(
            model_name="user",
            name="penalty_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18),
        ),
    ]
