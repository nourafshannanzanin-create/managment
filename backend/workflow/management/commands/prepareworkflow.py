from __future__ import annotations

import os

from django.core.management import BaseCommand, call_command

from workflow.models import User
from workflow.seed import seed_demo_data


def env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = "Apply migrations and optionally seed the database for container startup."

    def add_arguments(self, parser):
        parser.add_argument("--skip-migrate", action="store_true")
        parser.add_argument("--skip-seed", action="store_true")

    def handle(self, *args, **options):
        should_migrate = not options["skip_migrate"] and env_bool("WORKFLOW_AUTO_INIT_DB", True)
        should_seed = not options["skip_seed"] and env_bool("WORKFLOW_AUTO_SEED_DB", True)

        if should_migrate:
            call_command("migrate", interactive=False)

        if should_seed and not User.objects.exists():
            seed_demo_data()
            self.stdout.write(self.style.SUCCESS("Workflow demo data seeded."))
        else:
            self.stdout.write(self.style.SUCCESS("Workflow database is ready."))
