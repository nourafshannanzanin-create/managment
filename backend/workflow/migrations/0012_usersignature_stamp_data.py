from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("workflow", "0011_registrationrequest")]

    operations = [
        migrations.AddField(
            model_name="usersignature",
            name="stamp_data",
            field=models.TextField(blank=True, default=""),
        ),
    ]
