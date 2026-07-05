from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0004_sectionaccessgrant"),
    ]

    operations = [
        migrations.CreateModel(
            name="Wallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("key", models.CharField(max_length=40)),
                ("name", models.CharField(max_length=120)),
                ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("low_balance_threshold", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wallets", to="workflow.organization")),
            ],
            options={
                "db_table": "wallets",
            },
        ),
        migrations.CreateModel(
            name="WalletTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("direction", models.CharField(max_length=12)),
                ("transaction_type", models.CharField(max_length=40)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=18)),
                ("balance_after", models.DecimalField(decimal_places=2, max_digits=18)),
                ("note", models.TextField(blank=True)),
                ("reference_id", models.CharField(blank=True, max_length=80)),
                ("transacted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="wallet_transactions", to="workflow.user")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wallet_transactions", to="workflow.organization")),
                ("wallet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="workflow.wallet")),
            ],
            options={
                "db_table": "wallet_transactions",
            },
        ),
        migrations.AddConstraint(
            model_name="wallet",
            constraint=models.UniqueConstraint(fields=("organization", "key"), name="uq_organization_wallet_key"),
        ),
        migrations.AddIndex(
            model_name="wallettransaction",
            index=models.Index(fields=["organization", "-transacted_at"], name="idx_wallet_tx_org_date"),
        ),
        migrations.AddIndex(
            model_name="wallettransaction",
            index=models.Index(fields=["wallet", "-transacted_at"], name="idx_wallet_tx_wallet_date"),
        ),
    ]
