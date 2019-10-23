from quiz.models import Word
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'import dictionary file'

    def handle(self, *args, **options):
        filename = "dictionary.csv"
        f = open(filename, "r", encoding="utf8")
        for line in f:
            s = line.replace('\n', '')
            s = s.split('-')
            words = s[1].split('،')
            for word in words:
                actual_word = word.replace(' ', '')
                if len(actual_word) > 15:
                    continue
                simple_word = actual_word.replace('آ', 'ا').replace('ی', 'ى')
                Word.objects.create(word=actual_word, simple_word=simple_word)
        self.stdout.write(self.style.SUCCESS('Done'))
