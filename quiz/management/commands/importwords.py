from quiz.models import Word
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'import words file'

    def handle(self, *args, **options):
        filename = "dictionary.csv"
        f = open(filename, "r", encoding="utf8")
        for ind, line in enumerate(f):
            p = line.split('-')[1]
            for word in p.split('،'):
                self.stdout.write(self.style.SUCCESS(str(ind)))
                # actual_word = word.strip().replace('i', 'İ').replace('ı', 'I').upper()
                actual_word = word.strip().replace('آ', 'ا')
                if len(actual_word) < 2 or len(actual_word) > 8 or ' ' in actual_word:
                    continue
                simple_word = actual_word.replace('آ', 'ا').replace('ی', 'ى')
                Word.objects.filter(word=actual_word).delete()
                Word.objects.create(word=actual_word, simple_word=simple_word)
        self.stdout.write(self.style.SUCCESS('Done'))
