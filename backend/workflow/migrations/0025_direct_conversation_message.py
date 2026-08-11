from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0024_organization_city_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="DirectConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("pair_key", models.CharField(db_index=True, max_length=64)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="direct_conversations",
                        to="workflow.organization",
                    ),
                ),
            ],
            options={
                "db_table": "direct_conversations",
            },
        ),
        migrations.CreateModel(
            name="DirectConversationMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_read_at", models.DateTimeField(blank=True, null=True)),
                ("joined_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="workflow.directconversation",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="direct_conversation_memberships",
                        to="workflow.user",
                    ),
                ),
            ],
            options={
                "db_table": "direct_conversation_members",
            },
        ),
        migrations.CreateModel(
            name="DirectMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("body", models.TextField()),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="workflow.directconversation",
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="direct_messages",
                        to="workflow.user",
                    ),
                ),
            ],
            options={
                "db_table": "direct_messages",
            },
        ),
        migrations.AddField(
            model_name="directconversation",
            name="participants",
            field=models.ManyToManyField(
                related_name="direct_conversations",
                through="workflow.DirectConversationMember",
                to="workflow.user",
            ),
        ),
        migrations.AddConstraint(
            model_name="directconversation",
            constraint=models.UniqueConstraint(fields=("organization", "pair_key"), name="uq_direct_conversation_pair"),
        ),
        migrations.AddIndex(
            model_name="directconversation",
            index=models.Index(fields=["organization", "-updated_at"], name="idx_direct_conv_org_updated"),
        ),
        migrations.AddConstraint(
            model_name="directconversationmember",
            constraint=models.UniqueConstraint(fields=("conversation", "user"), name="uq_direct_conversation_member"),
        ),
        migrations.AddIndex(
            model_name="directmessage",
            index=models.Index(fields=["conversation", "created_at"], name="idx_direct_msg_conv_date"),
        ),
    ]
