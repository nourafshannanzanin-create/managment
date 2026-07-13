from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0015_user_finance_updated_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeaturePurchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("feature_key", models.CharField(db_index=True, max_length=60)),
                ("title", models.CharField(max_length=140)),
                ("payment_plan", models.CharField(default="cash", max_length=24)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("paid_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("remaining_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("next_installment_due_at", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "organization",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feature_purchases", to="workflow.organization"),
                ),
            ],
            options={
                "db_table": "feature_purchases",
            },
        ),
        migrations.AddConstraint(
            model_name="featurepurchase",
            constraint=models.UniqueConstraint(fields=("organization", "feature_key"), name="uq_organization_feature_purchase"),
        ),
    ]
