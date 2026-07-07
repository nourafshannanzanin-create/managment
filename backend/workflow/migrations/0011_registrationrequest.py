from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("workflow", "0010_alter_expenseapprovalassignment_status_and_more")]

    operations = [
        migrations.CreateModel(
            name="RegistrationRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("organization_name", models.CharField(max_length=180)),
                ("manager_name", models.CharField(max_length=120)),
                ("manager_username", models.CharField(max_length=80)),
                ("manager_email", models.EmailField(blank=True, max_length=160)),
                ("manager_phone", models.CharField(max_length=40)),
                ("manager_password_hash", models.CharField(max_length=255)),
                ("status", models.CharField(db_index=True, default="pending", max_length=24)),
                ("company_code", models.CharField(blank=True, max_length=80)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_organization", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="source_registration_request", to="workflow.organization")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_registration_requests", to="workflow.user")),
                ("ticket", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="registration_request", to="workflow.supportticket")),
            ],
            options={"db_table": "registration_requests"},
        ),
    ]
