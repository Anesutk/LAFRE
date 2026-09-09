from django.core.management.base import BaseCommand

from accounts.management.commands.test_account_helpers import TEST_PASSWORD, create_test_account
from accounts.models import UserProfile


class Command(BaseCommand):
    help = "Create or update an approved LAFRE test account."

    def add_arguments(self, parser):
        parser.add_argument("--role", choices=["student", "citizen", "lawyer"], required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--password", default=TEST_PASSWORD)

    def handle(self, *args, **options):
        role = options["role"]
        user = create_test_account(
            email=options["email"].strip().lower(),
            name=options["name"].strip(),
            role=getattr(UserProfile.Role, role.upper()),
            password=options["password"],
        )
        self.stdout.write(self.style.SUCCESS(f"Test {role} account ready: {user.email}"))
        self.stdout.write(f"Password: {options['password']}")
