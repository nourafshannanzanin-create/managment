from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0016_featurepurchase"),
    ]

    operations = [
        migrations.AddField(
            model_name="featurepurchase",
            name="renewal_due_at",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="featurepurchase",
            name="annual_subscription_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18),
        ),
        migrations.AddField(
            model_name="featurepurchase",
            name="annual_subscription_installment_months",
            field=models.IntegerField(default=0),
        ),
    ]
