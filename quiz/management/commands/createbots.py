from quiz.models import User
from django.core.management.base import BaseCommand, CommandError
import random
import math


class Command(BaseCommand):
    help = "Create bots"

    def add_arguments(self, parser):
        parser.add_argument("number", type=int)

    def handle(self, *args, **options):
        n = options.pop("number")
        BOT_NAMES = ['احمد', 'محمد رضا', 'سینا', 'رضا2386', 'شیرین', 'ندا', 'سیمن99', 'عباس', 'مهدی', 'نوش آفرین', 'مهراب']
        for i in range(min(len(BOT_NAMES), n)):
            user = User.objects.create_user(BOT_NAMES[i], None, 'qwerty123456')            
            user.is_bot = True
            user.save()
        self.stdout.write(self.style.SUCCESS("Done"))
