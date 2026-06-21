from django.core.management import call_command
from django.core.management.commands.runserver import Command as RunserverCommand

from workflow.seed import seed_demo_data


class Command(RunserverCommand):
    help = "Apply migrations, seed demo data, and run the Django server."

    def handle(self, *args, **options):
        call_command("migrate", interactive=False)
        seed_demo_data()
        super().handle(*args, **options)
