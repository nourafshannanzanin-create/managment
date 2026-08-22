from django.db import migrations


INDEXES = [
    ("idx_task_time_user_start", "task_time_entries", "(user_id, started_at)"),
    ("idx_audit_actor_date", "audit_logs", "(actor_id, created_at DESC)"),
    ("idx_request_requester_date", "requests", "(requester_id, created_at DESC)"),
    ("idx_expense_owner_date", "expenses", "(owner_id, expense_date DESC)"),
    ("idx_document_owner_date", "documents", "(owner_id, uploaded_at DESC)"),
]


def create_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return
    with schema_editor.connection.cursor() as cursor:
        for name, table, columns in INDEXES:
            cursor.execute(f"SHOW INDEX FROM {table}")
            existing = {row[2] for row in cursor.fetchall()}
            if name in existing:
                continue
            cursor.execute(f"CREATE INDEX {name} ON {table} {columns}")


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0033_request_approval_notes"),
    ]

    operations = [
        migrations.RunPython(create_indexes, migrations.RunPython.noop),
    ]
