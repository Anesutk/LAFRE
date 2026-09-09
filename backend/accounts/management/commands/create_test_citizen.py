from accounts.management.commands.create_test_account import Command as BaseCommand


class Command(BaseCommand):
    help = "Create or update an approved LAFRE test citizen account."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="test.citizen@example.test")
        parser.add_argument("--name", default="Test Citizen")
        parser.add_argument("--password", default="TestPass!2026")

    def handle(self, *args, **options):
        options.update({"role": "citizen"})
        return super().handle(*args, **options)
