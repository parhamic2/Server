from quiz.models import Level, RewardPackage
from django.core.management.base import BaseCommand, CommandError
import random
import math


class Command(BaseCommand):
    help = "Generate levels"

    def add_arguments(self, parser):
        parser.add_argument("number", type=str)

    def handle(self, *args, **options):
        Level.objects.exclude(level_id=0).delete()
        RewardPackage.objects.filter(kind='level').delete()
        levels_num = list(map(int, options.pop("number").split('.')))
        part = 0

        min_max_num_words = [
            [2, 2],
            [2, 3],
            [2, 4],
            [2, 5],
            [3, 5],
            [3, 6],
            [3, 6],
            [4, 6],
            [4, 7],
            [3, 8]
        ]

        min_max_words_length = [
            [2, 3],
            [2, 4],
            [2, 4],
            [3, 5],
            [3, 6],
            [3, 6],
            [2, 7],
            [3, 7],
            [3, 7],
            [3, 8]
        ]

        stage_reward = [
            100,
            100,
            100,
            140,
            140,
            140,
            200,
            200,
            300,
            300
        ]

        level_score = [
            5,
            10,
            20,
            30,
            50,
            80,
            120,
            150,
            200,
            300
        ]

        level_coin = [
            15,
            15,
            15,
            21,
            21,
            21,
            30,
            30,
            60,
            60
        ]

        level_time = [
            30,
            60,
            90,
            120,
            120,
            120,
            150,
            150,
            180,
            240
        ]

        part_reward_coins = [
            100, 100, 150, 150, 250, 250, 350, 350, 500, 800
        ]

        part_reward_copouns = [
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10
        ]

        for n in levels_num:
            for i in range(n):
                level = Level()
                level.extra_letters = 0
                level.season = "1"
                level.part = part
                num_words = random.randint(min_max_num_words[part][0], min_max_num_words[part][1])
                num_word_based_on_length = {}
                added_extra_leter_mark = {}
                for j in range(num_words):
                    prop = "num_questions_length{}".format(
                        random.randint(min_max_words_length[part][0], min_max_words_length[part][1])
                    )
                    setattr(level, prop, getattr(level, prop, 0) + 1)
                    num_word_based_on_length[prop] = (
                        num_word_based_on_length.get(prop, 0) + 1
                    )
                    if num_word_based_on_length[prop] > 2 and prop not in added_extra_leter_mark:
                        level.extra_letters += 1
                        added_extra_leter_mark[prop] = 1
                if level.num_questions_length2 >= 2:
                    level.num_questions_length3 += 1
                    level.num_questions_length2 = 1
                if i == n-1:
                    reward_package = RewardPackage.objects.create(kind='level', coins=part_reward_coins[part], copouns=part_reward_copouns[part])
                    level.reach_reward_package = reward_package
                    level.reach_reward = stage_reward[part]
                elif (i+1) % 14 == 0:
                    level.reach_reward = stage_reward[part]
                level.level_id = 10000 + level.part * 1000 + (i+1)
                if level.level_id == 10001:
                    for i in range(2, 9):
                        setattr(level, 'num_questions_length{}'.format(i), 0)
                    level.num_questions_length2 = 1
                    level.num_questions_length4 = 1
                    num_words = 2
                    level.extra_letters = 0
                level.time = level_time[part]
                level.score = level_score[part]
                level.coin = level_coin[part]
                level.save()
            part += 1
        self.stdout.write(self.style.SUCCESS("Done"))
