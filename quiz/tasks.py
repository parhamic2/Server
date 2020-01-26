import time
import sys
import os
import django
import random
from quiz.models import User, Match, MatchGame, Level, Lottery, Message, PlayRecord
from quiz.tournoment import Tournoment
from django.utils import timezone
from quiz.utils import create_match, get_time
from quiz.message_handlers import LevelCompleteHandler

from celery import shared_task


GLOBAL_DELAY = 8

@shared_task
def alive_message(id, msgs):
    user = User.objects.get(id=id)
    queryset = []
    for msg in msgs:
        obj = Message.objects.get(id=msg)
        if obj.perminent:
            obj.hidden = True
            obj.save()
        else:
            obj.delete()

    user.check_boost_expire()

@shared_task
def send_notification(user_id, title, content, image=None):
    user = User.objects.get(id=user_id)
    user.send_notification(title, content, image)

@shared_task
def update_matches():
    from constance import config

    MatchLevel = Level.objects.get(level_id=0)
    MatchGame.objects.filter(
        user__is_bot=True,
        state="WAITING",
        match__created__lt=get_time() - timezone.timedelta(seconds=9),
        start_time__lte=get_time()
    ).update(state="PLAYING")
    bot_games = MatchGame.objects.filter(
        user__is_bot=True,
        state="PLAYING",
        start_time__lt=get_time() - timezone.timedelta(seconds=40),
    )
    for game in bot_games:
        if game.match.state == "PENDING":
            game.match.state = "STARTED"
            game.match.save()
        LevelCompleteHandler.complete_game(
            game, int(random.randint(0, MatchLevel.get_total_words() ** 2) ** 0.5)
        )

@shared_task
def clear_guests():
    User.objects.filter(username__startswith="GUEST#").delete()

@shared_task
def update_matches2():
    from constance import config
    MatchLevel = Level.objects.get(level_id=0)
    idle_games = MatchGame.objects.filter(
        user__is_bot=False,
        state="PLAYING",
        start_time__lt=get_time()
        - timezone.timedelta(seconds=MatchLevel.time + GLOBAL_DELAY),
    )
    for game in idle_games:
        LevelCompleteHandler.complete_game(game, 0)

    idle_matches = Match.objects.exclude(state="FINISHED").filter(
        created__lt=get_time() - timezone.timedelta(hours=config.MATCH_EXPIRE_TIME),
    )
    for match in idle_matches:
        match.give_rewards()

def handle_queued_players(players, tournoment=None):
    idle_players = players.filter(
        last_alive_message__lt=get_time() - timezone.timedelta(seconds=2+ GLOBAL_DELAY)
    )
    for pl in idle_players:
        pl.send_message("queue", {"in_queue": False})
        pl.in_queue = False
        pl.save()
    players = players.filter(in_queue=True)
    print("{} players in queue".format(players.count()))
    i = 0
    while i < players.count():
        if i + 1 < players.count():  # there is another player
            match = create_match(
                [players[i], players[i + 1]], "STARTED", tournoment=tournoment
            )

            for user in match.users.all():
                user.in_queue = False
                user.save()
                user.send_message("start_match", {"match_id": str(match.pk)})
        elif players[i].queued_time < get_time() - timezone.timedelta(seconds=10):
            match = create_match(
                [players[i]], "STARTED", players[i], tournoment=tournoment
            )

            for user in match.users.all():
                user.in_queue = False
                user.save()
                user.send_message("start_match", {"match_id": str(match.pk)})

            print ('Match made with bot !!!!!!!!!!')

        i += 2


@shared_task
def matchmaking():
    queued_players = User.objects.filter(in_queue=True)
    players = queued_players.filter(queued_tournoment=None)
    handle_queued_players(players)
    tournoments = Tournoment.objects.all()
    for tournoment in tournoments:
        players = queued_players.filter(queued_tournoment=tournoment)
        handle_queued_players(players, tournoment=tournoment)

@shared_task
def bot_invite_reply():
    bots = User.objects.filter(is_bot=True)
    for bot in bots:
        pending_matches = bot.matches.filter(state='PENDING')
        from .message_handlers import InvitePlayerHandler
        for match in pending_matches:
            accept = (random.randint(0, 100) < 35)
            if accept:
                InvitePlayerHandler.invite(bot, match.user_created, True)
            else:
                InvitePlayerHandler.reject(bot, match.user_created)                

@shared_task
def lottery():
    lotteries = Lottery.objects.all()
    for lottery in lotteries:
        if (
            lottery.automatic
            and lottery.state == "OPEN"
            and lottery.last_active_time
            < get_time() - timezone.timedelta(days=lottery.days)
        ):
            lottery.state = "CLOSED"
            lottery.save()
            lottery.state = "STARTED"
            lottery.save()

@shared_task
def cycle():
    old_messages = Message.objects.filter(created__lt=get_time()-timezone.timedelta(hours=4), perminent=False)
    old_messages.delete()

    # boost expire
    # expired_boosts = User.objects.exclude(boost_expire=None).filter(boost_expire__lt=get_time())
    # for user in expired_boosts:
    #     user.boost = 1
    #     user.boost_expire = None
    #     user.save()


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quiz_project.settings")
    django.setup()

    i = 0
    while True:
        print("---------------{}".format(i))
        update_matches()
        matchmaking()
        lottery()
        time.sleep(1)
        i += 1
