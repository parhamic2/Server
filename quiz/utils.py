from .models import Match, MatchGame, User
from django.utils import timezone
from django.db.models.query import QuerySet
import random
from django.core.mail import EmailMessage


def send_email(email, subject, text):
    email_message = EmailMessage(subject, text, to=[email])
    email_message.send()

def get_time():
    return timezone.localtime(timezone.now())


def serialize(obj):
    if isinstance(obj, QuerySet):
        return serialize(list(obj))
    if not isinstance(obj, (dict, str, float, int, list)):
        return str(obj)
    if isinstance(obj, int) and not isinstance(obj, bool):
        return str(obj)
    if isinstance(obj, float):
        return str(obj)
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = serialize(obj[i])
        return obj
    if isinstance(obj, dict):
        for key in obj:
            obj[key] = serialize(obj[key])
        return obj
    return obj


def create_match(
    users, state="STARTED", user_created=None, turned_base=False, tournoment=None
):
    if user_created is None:
        user_created = users[0]
    match = Match.objects.create(
        user_created=user_created,
        tournoment=tournoment,
        state=state,
        turned_base=False,  # TODO
    )
    match.users.add(users[0])
    # fill with bot if there is just one user !
    if len(users) < 2:
        match.users.add(random.choice(list(User.objects.filter(is_bot=True))))
    else:
        match.users.add(users[1])

    match.save()

    # create games
    for g in range(3):
        MatchGame.objects.create(match=match, user=match.users.first(), row=g)
        MatchGame.objects.create(match=match, user=match.users.last(), row=g)
    # select first game
    if turned_base:
        match.games.filter(user=user_created, row=0).update(state="WAITING")
    else:
        match.games.filter(row=0).update(state="WAITING")

    if len(users) < 2:
        first_bot_match = match.games.filter(user__isbot=True, row=0).first()
        first_bot_match.start_time = get_time() + timezone.timedelta(seconds=9)
        first_bot_match.save()

    return match
