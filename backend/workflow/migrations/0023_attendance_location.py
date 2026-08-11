from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0022_user_avatar_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="organizationpreference",
            name="attendance_latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="organizationpreference",
            name="attendance_longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="organizationpreference",
            name="attendance_location_label",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="organizationpreference",
            name="attendance_radius_meters",
            field=models.PositiveIntegerField(default=20),
        ),
        migrations.AddField(
            model_name="attendanceevent",
            name="latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attendanceevent",
            name="longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attendanceevent",
            name="distance_meters",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
