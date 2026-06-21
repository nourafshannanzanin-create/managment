from django.core.management.base import BaseCommand

from workflow.seed import seed_demo_data


class Command(BaseCommand):
    help = "Seed demo workflow data"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **options):
        seed_demo_data(reset=options["reset"])
        self.stdout.write(self.style.SUCCESS("Workflow demo data is ready."))
