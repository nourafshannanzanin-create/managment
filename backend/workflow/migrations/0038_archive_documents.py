from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0037_idempotency_record"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArchiveDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("code", models.CharField(db_index=True, max_length=40, unique=True)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True, default="")),
                ("document_date", models.DateField(db_index=True)),
                ("file_name", models.CharField(max_length=255)),
                ("original_name", models.CharField(blank=True, default="", max_length=255)),
                ("mime_type", models.CharField(blank=True, default="", max_length=120)),
                ("size_bytes", models.PositiveIntegerField(default=0)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "department",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="archive_documents",
                        to="workflow.department",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="archive_documents",
                        to="workflow.organization",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="archive_documents",
                        to="workflow.user",
                    ),
                ),
            ],
            options={
                "db_table": "archive_documents",
            },
        ),
        migrations.CreateModel(
            name="ArchiveReferral",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("note", models.TextField(blank=True, default="")),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="referrals",
                        to="workflow.archivedocument",
                    ),
                ),
                (
                    "referred_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="archive_referrals_made",
                        to="workflow.user",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="archive_referrals",
                        to="workflow.user",
                    ),
                ),
            ],
            options={
                "db_table": "archive_referrals",
            },
        ),
        migrations.AddIndex(
            model_name="archivedocument",
            index=models.Index(fields=["organization", "-document_date"], name="idx_archive_org_date"),
        ),
        migrations.AddIndex(
            model_name="archivedocument",
            index=models.Index(fields=["owner", "-created_at"], name="idx_archive_owner_created"),
        ),
        migrations.AddIndex(
            model_name="archivereferral",
            index=models.Index(fields=["user", "-created_at"], name="idx_archive_ref_user"),
        ),
        migrations.AddConstraint(
            model_name="archivereferral",
            constraint=models.UniqueConstraint(fields=("document", "user"), name="uq_archive_document_user"),
        ),
    ]
