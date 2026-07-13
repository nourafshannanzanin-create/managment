from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0010_alter_expenseapprovalassignment_status_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="insurance_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18),
        ),
        migrations.CreateModel(
            name="EmployeeInsurancePayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("month", models.CharField(db_index=True, max_length=7)),
                ("base_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("paid_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_insurance_payments", to="workflow.user")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="employee_insurance_payments", to="workflow.organization")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="insurance_payments", to="workflow.user")),
            ],
            options={
                "db_table": "employee_insurance_payments",
            },
        ),
        migrations.AddConstraint(
            model_name="employeeinsurancepayment",
            constraint=models.UniqueConstraint(fields=("organization", "user", "month"), name="uq_employee_insurance_payment_month"),
        ),
    ]
