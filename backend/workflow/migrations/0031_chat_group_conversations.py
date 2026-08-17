from django.db import migrations, models
import django.db.models.deletion


def add_group_chat_fields(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute("SHOW COLUMNS FROM direct_conversations")
        existing = {row[0] for row in cursor.fetchall()}

        if "conversation_type" not in existing:
            cursor.execute(
                "ALTER TABLE direct_conversations "
                "ADD COLUMN conversation_type varchar(16) NOT NULL DEFAULT 'direct'"
            )
        if "title" not in existing:
            cursor.execute(
                "ALTER TABLE direct_conversations "
                "ADD COLUMN title varchar(120) NOT NULL DEFAULT ''"
            )
        if "created_by_id" not in existing:
            cursor.execute(
                "ALTER TABLE direct_conversations "
                "ADD COLUMN created_by_id bigint NULL"
            )
            cursor.execute(
                "ALTER TABLE direct_conversations "
                "ADD CONSTRAINT direct_conversations_created_by_id_fk "
                "FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL"
            )

        cursor.execute("SHOW INDEX FROM direct_conversations")
        indexes = {row[2] for row in cursor.fetchall()}
        if "idx_direct_conv_org_type" not in indexes:
            cursor.execute(
                "CREATE INDEX idx_direct_conv_org_type "
                "ON direct_conversations (organization_id, conversation_type)"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0030_user_entrusted_item"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_group_chat_fields, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="directconversation",
                    name="conversation_type",
                    field=models.CharField(
                        choices=[("direct", "خصوصی"), ("group", "گروهی")],
                        db_index=True,
                        default="direct",
                        max_length=16,
                    ),
                ),
                migrations.AddField(
                    model_name="directconversation",
                    name="title",
                    field=models.CharField(blank=True, default="", max_length=120),
                ),
                migrations.AddField(
                    model_name="directconversation",
                    name="created_by",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_chat_conversations",
                        to="workflow.user",
                    ),
                ),
                migrations.AddIndex(
                    model_name="directconversation",
                    index=models.Index(fields=["organization", "conversation_type"], name="idx_direct_conv_org_type"),
                ),
            ],
        ),
    ]
