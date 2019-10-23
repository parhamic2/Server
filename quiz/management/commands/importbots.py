from quiz.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'import bots file'

    def handle(self, *args, **options):
        filename = "usernames.txt"
        f = open(filename, "r", encoding="utf8")
        for line in f:
            if len(line) < 4:
                continue
            User.objects.create_user(line.strip(), None, 'qwerty', is_bot=True)
        f.close()
        self.stdout.write(self.style.SUCCESS('Done'))
