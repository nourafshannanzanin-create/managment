from django.db import migrations


INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_task_time_user_start ON task_time_entries (user_id, started_at)",
    "CREATE INDEX IF NOT EXISTS idx_audit_actor_date ON audit_logs (actor_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_request_requester_date ON requests (requester_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_expense_owner_date ON expenses (owner_id, expense_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_document_owner_date ON documents (owner_id, uploaded_at DESC)",
]


def create_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return
    with schema_editor.connection.cursor() as cursor:
        for statement in INDEX_STATEMENTS:
            cursor.execute(statement)


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0033_request_approval_notes"),
    ]

    operations = [
        migrations.RunPython(create_indexes, migrations.RunPython.noop),
    ]
