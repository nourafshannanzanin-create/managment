from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0019_delete_employeeinsurancepayment"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="platform_role",
            field=models.CharField(
                blank=True,
                choices=[("", ""), ("hq_admin", "HQ Admin"), ("hq_support", "HQ Support")],
                default="",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="support_star_rating",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AddField(
            model_name="user",
            name="support_rating_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="support_customer_satisfaction_avg",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AddField(
            model_name="user",
            name="support_response_quality_avg",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AddField(
            model_name="user",
            name="support_first_response_minutes_avg",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name="user",
            name="support_total_responses",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="support_resolved_tickets_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="support_last_scored_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="deleted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="deleted_users",
                to="workflow.user",
            ),
        ),
        migrations.AddField(
            model_name="supportticket",
            name="response_text",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="supportticket",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_support_tickets",
                to="workflow.user",
            ),
        ),
        migrations.AddField(
            model_name="supportticket",
            name="response_quality_score",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AddField(
            model_name="supportticket",
            name="last_message_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="supportmessage",
            name="is_internal",
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["assigned_to", "-last_message_at"], name="idx_support_ticket_assignee"),
        ),
        migrations.RunSQL(
            sql="UPDATE users SET platform_role = 'hq_admin' WHERE slug = 'milad_dhs'",
            reverse_sql="UPDATE users SET platform_role = '' WHERE slug = 'milad_dhs'",
        ),
    ]
