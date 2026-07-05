from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0005_wallet_wallettransaction"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupportTicket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("subject", models.CharField(max_length=180)),
                ("message", models.TextField()),
                ("category", models.CharField(choices=[("technical", "Technical"), ("financial", "Financial"), ("operations", "Operations"), ("account", "Account"), ("other", "Other")], default="technical", max_length=32)),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")], default="medium", max_length=32)),
                ("status", models.CharField(choices=[("open", "Open"), ("pending", "Pending"), ("answered", "Answered"), ("closed", "Closed")], default="open", max_length=32)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("first_response_at", models.DateTimeField(blank=True, null=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("customer_satisfaction", models.IntegerField(blank=True, null=True)),
                ("customer_feedback", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_tickets", to="workflow.organization")),
                ("requester", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="support_tickets", to="workflow.user")),
                ("responded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="answered_support_tickets", to="workflow.user")),
            ],
            options={
                "db_table": "support_tickets",
            },
        ),
        migrations.CreateModel(
            name="SupportMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("sender_name", models.CharField(max_length=120)),
                ("sender_platform_role", models.CharField(blank=True, max_length=32)),
                ("body", models.TextField()),
                ("sender", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="support_messages", to="workflow.user")),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="workflow.supportticket")),
            ],
            options={
                "db_table": "support_messages",
            },
        ),
        migrations.CreateModel(
            name="SupportAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("original_name", models.CharField(max_length=255)),
                ("stored_name", models.CharField(max_length=255)),
                ("mime_type", models.CharField(blank=True, max_length=120, null=True)),
                ("size_bytes", models.IntegerField(default=0)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="workflow.supportticket")),
            ],
            options={
                "db_table": "support_attachments",
            },
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["organization", "-updated_at"], name="idx_support_ticket_org_date"),
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["status", "-updated_at"], name="idx_support_ticket_status"),
        ),
        migrations.AddIndex(
            model_name="supportmessage",
            index=models.Index(fields=["ticket", "created_at"], name="idx_support_msg_ticket_date"),
        ),
    ]
