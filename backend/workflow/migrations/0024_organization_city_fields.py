from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0023_attendance_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="province_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="province_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="organization",
            name="city_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="city_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="registrationrequest",
            name="province_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="registrationrequest",
            name="province_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="registrationrequest",
            name="city_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="registrationrequest",
            name="city_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
    ]
