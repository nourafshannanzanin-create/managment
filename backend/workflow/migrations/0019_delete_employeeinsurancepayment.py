from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0018_attendance_event"),
    ]

    operations = [
        migrations.DeleteModel(
            name="EmployeeInsurancePayment",
        ),
    ]
